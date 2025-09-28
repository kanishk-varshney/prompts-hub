from nicegui import ui, app
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional
import json

from models import Prompt, Tag, PromptVersion, PromptCreate, PromptUpdate, PromptTag
from db import get_session

# Global variables for UI state
prompts_table = None
current_prompts = []
filter_model = ""
filter_tags = []
search_text = ""

# Model types for dropdown - easily configurable
MODEL_TYPES = [
    "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini",
    "gpt-3.5-turbo", "gpt-3.5-turbo-16k",
    "claude-3-opus", "claude-3-sonnet", "claude-3-haiku", "claude-2", "claude-instant",
    "llama-2-7b", "llama-2-13b", "llama-2-70b", "llama-3-8b", "llama-3-70b",
    "gemini-pro", "gemini-pro-vision", "gemini-1.5-pro", "gemini-1.5-flash",
    "mistral-7b", "mixtral-8x7b", "codellama-34b",
    "other"
]


def get_all_prompts(session: Session, model_filter: str = "", tag_filter: List[str] = None, search: str = "") -> List[Prompt]:
    """Get all prompts with optional filtering"""
    query = select(Prompt).options(selectinload(Prompt.tags))

    # Apply model filter
    if model_filter:
        query = query.where(Prompt.model_type == model_filter)

    # Apply search filter
    if search:
        query = query.where(
            (Prompt.title.contains(search)) |
            (Prompt.content.contains(search))
        )

    prompts = session.exec(query).all()

    # Apply tag filter (done in Python for simplicity)
    if tag_filter:
        filtered_prompts = []
        for prompt in prompts:
            prompt_tag_names = [tag.name for tag in prompt.tags]
            if any(tag in prompt_tag_names for tag in tag_filter):
                filtered_prompts.append(prompt)
        return filtered_prompts

    return prompts


def get_all_tags(session: Session) -> List[Tag]:
    """Get all tags"""
    return session.exec(select(Tag)).all()


def create_or_get_tags(session: Session, tag_names: List[str]) -> List[Tag]:
    """Create new tags or get existing ones"""
    tags = []
    for name in tag_names:
        name = name.strip()
        if not name:
            continue
        
        # Try to get existing tag
        existing_tag = session.exec(select(Tag).where(Tag.name == name)).first()
        if existing_tag:
            tags.append(existing_tag)
        else:
            # Create new tag
            new_tag = Tag(name=name)
            session.add(new_tag)
            session.commit()
            session.refresh(new_tag)
            tags.append(new_tag)
    
    return tags


def sanitize_title(title: str) -> str:
    """Sanitize and format the title properly"""
    if not title:
        return ""

    # Remove extra whitespace and capitalize properly
    title = " ".join(title.split())  # Remove extra spaces
    title = title.title()  # Title case (capitalizes first letter of each word)

    return title


def copy_to_clipboard(text: str):
    """Copy text to clipboard using JavaScript"""
    ui.run_javascript(f'''
        navigator.clipboard.writeText(`{text.replace("`", "\\`")}`).then(() => {{
            console.log('Copied to clipboard');
        }});
    ''')
    ui.notify("Copied to clipboard!", type="positive")


def refresh_table():
    """Refresh the prompts table"""
    global prompts_table, current_prompts
    
    with next(get_session()) as session:
        current_prompts = get_all_prompts(session, filter_model, filter_tags, search_text)
    
    if prompts_table:
        prompts_table.clear()
        with prompts_table:
            create_table_content()


def create_table_content():
    """Create table content with prompts"""
    if not current_prompts:
        ui.label("No prompts found").classes("text-gray-500 text-center p-4")
        return
    
    for prompt in current_prompts:
        with ui.card().classes("w-full mb-4 p-4"):
            with ui.row().classes("w-full items-center justify-between"):
                with ui.column().classes("flex-grow"):
                    ui.label(prompt.title).classes("text-lg font-bold")
                    ui.label(f"Model: {prompt.model_type} | Version: {prompt.version}").classes("text-sm text-gray-600")
                    
                    # Tags
                    if prompt.tags:
                        with ui.row().classes("gap-1 mt-1"):
                            for tag in prompt.tags:
                                ui.badge(tag.name).classes("bg-blue-100 text-blue-800")
                
                # Action buttons
                with ui.row().classes("gap-2"):
                    ui.button("📋", on_click=lambda p=prompt: copy_to_clipboard(p.content)).props("flat dense").tooltip("Copy")
                    ui.button("✏️", on_click=lambda p=prompt: open_edit_dialog(p)).props("flat dense").tooltip("Edit")
                    ui.button("🕒", on_click=lambda p=prompt: open_versions_dialog(p)).props("flat dense").tooltip("Versions")
                    ui.button("🗑️", on_click=lambda p=prompt: delete_prompt(p.id)).props("flat dense color=negative").tooltip("Delete")
            
            # Content preview (first 200 chars)
            content_preview = prompt.content[:200] + "..." if len(prompt.content) > 200 else prompt.content
            ui.label(content_preview).classes("text-sm text-gray-700 mt-2 font-mono bg-gray-50 p-2 rounded")


def open_add_dialog():
    """Open dialog to add new prompt"""
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Add New Prompt").classes("text-lg font-bold mb-4")
        
        title_input = ui.input("Title").classes("w-full")
        model_select = ui.select(MODEL_TYPES, label="Model Type").classes("w-full")
        content_input = ui.textarea("Content").classes("w-full").props("rows=8")
        tags_input = ui.input("Tags (comma-separated)").classes("w-full")
        
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=lambda: save_new_prompt(
                dialog, title_input.value, model_select.value, 
                content_input.value, tags_input.value
            )).props("color=primary")
    
    dialog.open()


def save_new_prompt(dialog, title: str, model_type: str, content: str, tags_str: str):
    """Save new prompt to database"""
    if not title or not model_type or not content:
        ui.notify("Please fill all required fields", type="negative")
        return

    # Sanitize the title
    title = sanitize_title(title)

    with next(get_session()) as session:
        # Create tags
        tag_names = [name.strip() for name in tags_str.split(",") if name.strip()]
        tags = create_or_get_tags(session, tag_names)

        # Create prompt
        prompt = Prompt(
            title=title,
            content=content,
            model_type=model_type,
            version="1.0"
        )
        
        session.add(prompt)
        session.commit()
        session.refresh(prompt)
        
        # Add tags
        for tag in tags:
            prompt.tags.append(tag)
        
        session.commit()
    
    ui.notify("Prompt saved successfully!", type="positive")
    dialog.close()
    refresh_table()


def open_edit_dialog(prompt: Prompt):
    """Open dialog to edit existing prompt"""
    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Edit Prompt").classes("text-lg font-bold mb-4")
        
        title_input = ui.input("Title", value=prompt.title).classes("w-full")
        model_select = ui.select(MODEL_TYPES, label="Model Type", value=prompt.model_type).classes("w-full")
        content_input = ui.textarea("Content", value=prompt.content).classes("w-full").props("rows=8")
        
        # Current tags
        current_tag_names = [tag.name for tag in prompt.tags]
        tags_input = ui.input("Tags (comma-separated)", value=", ".join(current_tag_names)).classes("w-full")
        
        with ui.row().classes("w-full justify-end gap-2 mt-4"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Save", on_click=lambda: save_edited_prompt(
                dialog, prompt.id, title_input.value, model_select.value,
                content_input.value, tags_input.value, prompt.version
            )).props("color=primary")
    
    dialog.open()


def save_edited_prompt(dialog, prompt_id: int, title: str, model_type: str, content: str, tags_str: str, current_version: str):
    """Save edited prompt and create version history"""
    if not title or not model_type or not content:
        ui.notify("Please fill all required fields", type="negative")
        return

    # Sanitize the title
    title = sanitize_title(title)

    with next(get_session()) as session:
        prompt = session.get(Prompt, prompt_id)
        if not prompt:
            ui.notify("Prompt not found", type="negative")
            return
        
        # Save current version to history if content changed
        if prompt.content != content:
            version_history = PromptVersion(
                prompt_id=prompt.id,
                content=prompt.content,
                version=prompt.version
            )
            session.add(version_history)
            
            # Increment version
            version_parts = current_version.split(".")
            if len(version_parts) == 2:
                major, minor = int(version_parts[0]), int(version_parts[1])
                prompt.version = f"{major}.{minor + 1}"
            else:
                prompt.version = "1.1"
        
        # Update prompt
        prompt.title = title
        prompt.content = content
        prompt.model_type = model_type
        prompt.updated_at = datetime.now()
        
        # Update tags
        prompt.tags.clear()
        tag_names = [name.strip() for name in tags_str.split(",") if name.strip()]
        tags = create_or_get_tags(session, tag_names)
        for tag in tags:
            prompt.tags.append(tag)
        
        session.commit()
    
    ui.notify("Prompt updated successfully!", type="positive")
    dialog.close()
    refresh_table()


def open_versions_dialog(prompt: Prompt):
    """Open dialog to view prompt versions"""
    with next(get_session()) as session:
        # Get fresh prompt with versions
        fresh_prompt = session.get(Prompt, prompt.id)
        versions = fresh_prompt.versions
    
    with ui.dialog() as dialog, ui.card().classes("w-full max-w-4xl"):
        ui.label(f"Version History: {prompt.title}").classes("text-lg font-bold mb-4")
        
        if not versions:
            ui.label("No version history available").classes("text-gray-500")
        else:
            for version in sorted(versions, key=lambda v: v.created_at, reverse=True):
                with ui.card().classes("w-full mb-2 p-3"):
                    with ui.row().classes("w-full items-center justify-between"):
                        ui.label(f"Version {version.version}").classes("font-bold")
                        ui.label(version.created_at.strftime("%Y-%m-%d %H:%M")).classes("text-sm text-gray-600")
                        ui.button("📋", on_click=lambda v=version: copy_to_clipboard(v.content)).props("flat dense").tooltip("Copy")
                    
                    content_preview = version.content[:300] + "..." if len(version.content) > 300 else version.content
                    ui.label(content_preview).classes("text-sm font-mono bg-gray-50 p-2 rounded mt-2")
        
        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("Close", on_click=dialog.close).props("flat")
    
    dialog.open()


def delete_prompt(prompt_id: int):
    """Delete prompt with confirmation"""
    with ui.dialog() as dialog, ui.card():
        ui.label("Are you sure you want to delete this prompt?").classes("mb-4")
        with ui.row().classes("gap-2"):
            ui.button("Cancel", on_click=dialog.close).props("flat")
            ui.button("Delete", on_click=lambda: confirm_delete(dialog, prompt_id)).props("color=negative")
    
    dialog.open()


def confirm_delete(dialog, prompt_id: int):
    """Confirm and delete prompt"""
    with next(get_session()) as session:
        prompt = session.get(Prompt, prompt_id)
        if prompt:
            session.delete(prompt)
            session.commit()
    
    ui.notify("Prompt deleted successfully!", type="positive")
    dialog.close()
    refresh_table()


def update_filters():
    """Update filters and refresh table"""
    global filter_model, filter_tags, search_text
    refresh_table()


@ui.page("/")
def main_page():
    """Main page with prompt management interface"""
    global prompts_table, filter_model, filter_tags, search_text
    
    # Header
    with ui.header().classes("bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg"):
        with ui.row().classes("w-full items-center justify-between px-4 py-3"):
            ui.label("🚀 Prompts Hub").classes("text-2xl font-bold")
            ui.button("➕ Add Prompt", on_click=open_add_dialog).props("color=white text-color=primary flat")
    
    # Filters
    with ui.card().classes("w-full mb-4"):
        with ui.row().classes("w-full gap-4 items-end"):
            # Model filter
            model_filter = ui.select(
                [""] + MODEL_TYPES, 
                label="Filter by Model", 
                value=""
            ).classes("flex-1")
            
            # Search
            search_input = ui.input("Search prompts...").classes("flex-2")
            
            # Tags filter (will be populated dynamically)
            with next(get_session()) as session:
                all_tags = get_all_tags(session)
                tag_options = [tag.name for tag in all_tags]
            
            tags_filter = ui.select(
                tag_options,
                label="Filter by Tags",
                multiple=True
            ).classes("flex-1")
            
            ui.button("🔍 Filter", on_click=lambda: apply_filters(
                model_filter.value, tags_filter.value, search_input.value
            )).props("color=primary")
    
    # Prompts table container
    prompts_table = ui.column().classes("w-full")
    
    # Initial load
    refresh_table()


def apply_filters(model: str, tags: List[str], search: str):
    """Apply filters and refresh table"""
    global filter_model, filter_tags, search_text
    filter_model = model or ""
    filter_tags = tags or []
    search_text = search or ""
    refresh_table()


if __name__ in {"__main__", "__mp_main__"}:
    import os
    # Configure NiceGUI for production
    port = int(os.getenv("PORT", 8080))
    ui.run(
        title="Prompts Hub",
        port=port,
        host="0.0.0.0",  # Allow external connections
        show=False,  # Don't auto-open browser
        reload=False
    )
