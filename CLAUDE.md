# Agent Steering Documentation

## Project Overview
This is a TypeScript/Vite web application that combines MCP (Model Context Protocol) servers with Google's Gemini AI to create an interactive AI assistant. The app provides a chat interface with specialized tools for Wild Kratts content and basic maps functionality.

## Architecture Components

### Core Files
- **index.tsx** - Main application entry point, connects MCP client to Gemini AI
- **mcp_maps_server.ts** - MCP server implementation with tools for maps, products, and episodes
- **playground.ts** - Lit-based UI component for chat interface and content display
- **package.json** - Dependencies include MCP SDK, Google GenAI, Lit, and Zod
- **vite.config.ts** - Build configuration with environment variable handling

### Key Dependencies
- `@modelcontextprotocol/sdk` - MCP protocol implementation
- `@google/genai` - Google Gemini AI integration  
- `lit` - Web components framework for UI
- `zod` - Schema validation
- `marked` - Markdown parsing with syntax highlighting

## MCP Tools Available

### 1. Maps Tools (Basic)
- `view_location_google_maps` - View specific location
- `search_google_maps` - Search for places near location
- `directions_on_google_maps` - Get directions between points
- **Note**: Returns textual confirmation only, no visual maps

### 2. Wild Kratts Products API
- `get-wild-kratts-products` - Fetch Wild Kratts merchandise
  - **Search Mode**: When `searchTerm` provided, searches catalog (up to 100 results)
  - **Browse Mode**: When no `searchTerm`, returns paginated list
  - **Filters**: Optional `category` and `page` parameters
  - **Categories**: "Accessorize", "Apps", "Bath & Body", "Bedding", "Celebrate", "Coloring", "Crafts & Activities", "Listen", "Play", "Posters", "Read", "STEM", "Watch", "Wear"

### 3. Wild Kratts Episodes API  
- `get-wild-kratts-episodes` - Fetch TV episode information
  - **Filters**: `seasonNumber`, `episodeTitle`, `animalsFeatured`
  - **Field Selection**: Optional `fields` parameter for efficiency
  - **Valid Fields**: "Season", "Episode Number (Broadcast Order)", "Episode Number (Internal)", "Episode Title", "Air Date", "imagePath", "Summary", "Animals Featured", "Creature Powers", "Locations", "streamingUrls"

## Development Commands

### Setup & Running
```bash
npm install                    # Install dependencies
npm run dev                   # Start development server
npm run build                 # Build for production
npm run preview               # Preview production build
```

### Environment Variables
- `GEMINI_API_KEY` - Required for Gemini AI integration (set in .env.local)

## Key Implementation Details

### AI System Instructions
The AI assistant is configured with detailed instructions for:
- Tool usage guidelines for products and episodes
- Search vs browse modes for products
- Field selection for efficient episode queries
- Complex query handling strategies

### UI Components
- **Playground Class**: Main Lit component managing chat state and content display
- **Chat Interface**: Supports message history, thinking indicators, status updates
- **Content Display**: Dynamic switching between products and episodes with expandable descriptions
- **Responsive Design**: Collapsible chat panel with toggle functionality

### Data Flow
1. User input → Gemini AI with MCP tools
2. AI calls appropriate MCP tools
3. Tool responses processed and displayed in UI
4. Chat messages and content cards updated reactively

## Agent Usage Guidelines

### When Working on This Project:
- **Content Tools**: Always use the MCP tools for Wild Kratts data - don't mock or fabricate product/episode information
- **API Integration**: The tools connect to real Wild Kratts APIs at wildkratts.com
- **UI State**: The playground component manages active content type (products vs episodes)
- **Error Handling**: Tools include built-in error handling and empty state management
- **Performance**: Use `fields` parameter for episode queries when doing analysis vs display

### Code Patterns:
- TypeScript with strict mode enabled
- Lit decorators for reactive properties
- Zod schemas for API validation
- Async/await for API calls
- Marked for markdown rendering with syntax highlighting

### Build & Deployment:
- Vite handles bundling and development server
- Environment variables loaded from .env.local
- No backend required - pure frontend with external API calls
- Uses ES modules and modern JavaScript features

## Testing & Debugging
- Check browser console for MCP tool call logs
- Verify GEMINI_API_KEY is set in environment
- Tools return JSON responses that are parsed and displayed
- UI state updates are reactive through Lit's property system