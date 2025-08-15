# Zillow Waterfront Properties Web App

A modern Next.js 15 web application for managing and exploring waterfront properties extracted from Zillow.

## Features

### 🏠 **Property Search & Viewing**
- Search **ALL properties** in your database (1,200+ properties)
- Advanced filtering options (beds, baths, waterfront status)
- Property detail views with comprehensive information
- Responsive design for all devices
- **Note**: Waterfront analysis data (dock info, measurements) is available for 634 properties where detailed extraction was possible

### ❤️ **Favorites & Comments**
- Save favorite properties to your personal collection
- Add personal notes and comments to properties
- Manage your favorites with easy add/remove functionality
- Track property value and statistics

### 🔄 **Property Extraction**
- Add new properties by extracting from Zillow search URLs
- Monitor extraction job progress in real-time
- Batch processing of multiple URLs
- Job management with start/stop/delete capabilities

### 🤖 **AI Property Agent**
- Ask natural language questions about your **complete property database**
- Get intelligent insights on market trends, pricing, and features
- Suggested questions for common queries
- Real-time chat interface with the AI agent
- **Note**: Can answer questions about all properties, with detailed waterfront analysis available for 634 properties

## Data Structure

### Database Tables
The web app connects to your existing Zillow Waterfront database with the following key tables:

#### Core Property Data
- `listings_summary` - **Primary table with ALL properties** (1,200+ properties)
- `listings_detail` - Detailed property data for all properties
- `property_photos` - Photo metadata and URLs for all properties

#### Waterfront Analysis (Best Effort)
- `wf_data` - **Waterfront analysis data for 634 properties** where detailed extraction was possible
- `listings_derived` - Computed and analyzed fields for properties with analysis
- `listing_text_content` - Extracted text content for properties with analysis

#### Web App Functionality
- `property_favorites` - User favorites
- `property_comments` - User comments  
- `extraction_jobs` - Extraction job tracking

### Important Notes
- **All 1,200+ properties are searchable and viewable**
- **Waterfront analysis data is only available for 634 properties** where we could extract detailed measurements
- **Missing waterfront data doesn't mean a property isn't waterfront** - it just means we couldn't extract specific measurements
- **The app gracefully handles missing waterfront analysis data** and shows what's available

## Tech Stack

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Database**: PostgreSQL with Prisma ORM
- **Icons**: Lucide React
- **UI Components**: Custom components with Radix UI primitives

## Getting Started

### Prerequisites

- Node.js 18+ 
- PostgreSQL database
- Access to your Zillow Waterfront database

### Installation

1. **Clone the repository**
   ```bash
   cd webapp
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your database connection string
   ```

4. **Set up the database**
   ```bash
   # Generate Prisma client
   npx prisma generate
   
   # Run database migrations (if needed)
   npx prisma db push
   ```

5. **Start the development server**
   ```bash
   npm run dev
   ```

6. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## Project Structure

```
webapp/
├── src/
│   ├── app/                 # Next.js App Router pages
│   │   ├── page.tsx        # Dashboard
│   │   ├── search/         # Property search
│   │   ├── favorites/      # User favorites
│   │   ├── extraction/     # Property extraction
│   │   └── ai-agent/       # AI chat interface
│   ├── components/         # Reusable UI components
│   └── config/            # Configuration files
├── prisma/                # Database schema and migrations
├── public/                # Static assets
└── package.json
```

## Development Phases

### Phase 1: Core Infrastructure ✅
- [x] Next.js 15 setup with TypeScript
- [x] Database schema and Prisma configuration
- [x] Basic navigation and layout
- [x] Dashboard with correct property counts

### Phase 2: Property Search & Viewing 🚧
- [x] Search interface with filters
- [x] Property listing components
- [x] Corrected to show all properties, not just waterfront analysis
- [ ] Database integration for real search
- [ ] Property detail pages
- [ ] Advanced filtering and sorting

### Phase 3: Favorites & Comments 🚧
- [x] Favorites management interface
- [x] Comments and notes system
- [ ] Database integration for persistence
- [ ] User authentication system

### Phase 4: Property Extraction 🚧
- [x] Extraction job management interface
- [x] URL input and processing
- [ ] Integration with Python extraction scripts
- [ ] Real-time job monitoring

### Phase 5: AI Agent 🚧
- [x] Chat interface with corrected responses
- [x] Updated to clarify coverage of all properties
- [ ] Integration with property database
- [ ] AI-powered insights and analysis
- [ ] Natural language query processing

## API Endpoints

The web app will include the following API routes:

- `GET /api/properties` - Search and filter **ALL properties**
- `GET /api/properties/[zpid]` - Get property details
- `GET /api/properties/[zpid]/waterfront-analysis` - Get waterfront analysis (if available)
- `POST /api/favorites` - Add/remove favorites
- `POST /api/comments` - Add/edit comments
- `POST /api/extraction` - Start extraction jobs
- `GET /api/extraction/[id]` - Get job status
- `POST /api/ai/chat` - AI agent chat endpoint

## Data Coverage

### Property Coverage
- **Total Properties**: 1,200+ (all properties in database)
- **Waterfront Properties**: 580+ (properties marked as waterfront)
- **Properties with Analysis**: 634 (properties with detailed waterfront measurements)

### Waterfront Analysis Coverage
The waterfront analysis data (`wf_data` table) contains detailed information for 634 properties including:
- Waterfront footage measurements
- Dock information and specifications
- Water depth and bridge height
- Canal width and access type
- Boat dock, lift, and ramp details

**Note**: This data is only available where the extraction process could successfully parse and measure these details. Properties without this data may still be waterfront properties.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the Zillow Waterfront Extractor system.

## Support

For questions or issues, please check the main project documentation or create an issue in the repository.
