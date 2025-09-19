# 🚀 Prompts Hub

A web-based prompt portal for managing, versioning, and organizing AI prompts. Built with NiceGUI, SQLModel, and SQLite for easy deployment.

## Features

- ✅ **CRUD Operations**: Create, read, update, delete prompts
- ✅ **Version History**: Automatic versioning when prompts are edited
- ✅ **Tagging System**: Organize prompts with tags
- ✅ **Filtering & Search**: Filter by model type, tags, and search content
- ✅ **Copy to Clipboard**: One-click copy of prompt content
- ✅ **Clean UI**: Simple, responsive interface with card-based layout

## Tech Stack

- **Frontend/UI**: NiceGUI (Python-based web framework)
- **Backend**: FastAPI (via NiceGUI)
- **Database**: SQLite (local) / Supabase (cloud-ready)
- **ORM**: SQLModel
- **Deployment**: Replit, Vercel, or any Python hosting

## Quick Start

### Prerequisites

- Python 3.12 or higher
- UV package manager (recommended)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd prompts-hub
```

### 2. Install UV (if not installed)

```bash
# On macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### 3. Install Dependencies

```bash
# Install project dependencies
uv sync
```

### 4. Run the Application

```bash
# Activate virtual environment
uv run python main.py
```

Or directly with UV:
```bash
uv run main.py
```

### 5. Open in Browser

Navigate to `http://localhost:8080`

## Project Structure

```
prompts-hub/
├── main.py          # Main NiceGUI application
├── models.py        # SQLModel database models
├── db.py           # Database connection and setup
├── pyproject.toml  # UV configuration and dependencies
└── README.md       # This file
```

## Usage

### Adding a Prompt
1. Click "➕ Add Prompt" in the header
2. Fill in title, select model type, enter content
3. Add tags (comma-separated)
4. Click "Save"

### Editing a Prompt
1. Click the "✏️" (edit) button on any prompt
2. Modify the content
3. Click "Save" (creates new version automatically)

### Copying a Prompt
1. Click the "📋" (copy) button on any prompt
2. Content is copied to clipboard

### Viewing Versions
1. Click the "🕒" (versions) button on any prompt
2. Select and copy from previous versions

### Filtering
- Use the dropdown to filter by model type
- Use multi-select for tags
- Use search box for text search
- Click "🔍 Filter" to apply

## Database Schema

### Prompts Table
- `id`: Primary key
- `title`: Prompt title
- `content`: Full prompt text
- `version`: Current version (e.g., "1.0", "1.1")
- `model_type`: AI model (gpt-4, claude, etc.)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### Tags Table
- `id`: Primary key
- `name`: Unique tag name

### Prompt Tags (Many-to-Many)
- `prompt_id`: Foreign key to prompts
- `tag_id`: Foreign key to tags

### Prompt Versions (History)
- `id`: Primary key
- `prompt_id`: Foreign key to prompts
- `content`: Version content
- `version`: Version number
- `created_at`: Version creation timestamp

## Deployment

### Replit (Recommended for MVP)
1. Create new Replit project
2. Upload all files
3. Run `python main.py`
4. Access via Replit URL

### Local Development
```bash
uv run main.py
```

### Production Deployment
For production, consider:
- **Supabase**: Replace SQLite with Supabase connection
- **Vercel/Docker**: Containerize the app
- **Railway/Fly.io**: Python hosting platforms

## Migration to Supabase

1. Create Supabase project
2. Get connection string
3. Set environment variable: `DATABASE_URL=postgresql://...`
4. The same SQLModel code works with Postgres

## Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

## License

MIT License - see LICENSE file for details
