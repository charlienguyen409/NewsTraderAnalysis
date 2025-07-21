# Analysis Service Updates - Market Summary Storage

## Overview

This document details the changes made to the analysis service to store market summaries in the database during both full analysis and headline analysis workflows.

## Changes Made

### 1. CRUD Service Updates (`backend/app/services/crud.py`)

**Added MarketSummaryCRUD class:**
- `create_market_summary()` - Store market summary in database
- `get_market_summary_by_session()` - Retrieve summary by session ID
- `get_market_summaries()` - List summaries with filtering
- Added `market_summary_crud` instance for use across services

**New imports:**
- `MarketSummary` model
- `MarketSummaryCreate` schema

### 2. Analysis Service Updates (`backend/app/services/analysis_service.py`)

**New imports:**
- `market_summary_crud` from CRUD services
- `AnalysisTypeEnum` from MarketSummary model
- `MarketSummaryCreate` schema

**Modified `_generate_market_summary()` method:**
- Added `analysis_type` parameter (defaults to "full")
- Enhanced logging to include analysis type
- **Database storage**: Creates `MarketSummaryCreate` object and stores via CRUD
- Includes metadata: session_id, analysis_type, model_used, data_sources
- Logs successful storage with summary ID
- Enhanced error handling with analysis type context

**Updated workflow calls:**
- `run_analysis()`: Calls with `analysis_type="full"`
- `run_headline_analysis()`: Calls with `analysis_type="headlines"`

## Implementation Details

### Market Summary Storage Flow

1. **LLM Generation**: Generate market summary via LLMService
2. **Metadata Preparation**: Create data_sources with counts
3. **Database Creation**: Create MarketSummaryCreate object with:
   - `session_id`: Links to analysis session
   - `summary_data`: Complete LLM-generated summary
   - `analysis_type`: FULL or HEADLINES enum
   - `model_used`: LLM model identifier
   - `data_sources`: Article/analysis/position counts
4. **Database Storage**: Store via `market_summary_crud.create_market_summary()`
5. **Activity Logging**: Log successful storage with summary ID

### Analysis Type Distinction

- **Full Analysis**: `analysis_type="full"` → `AnalysisTypeEnum.FULL`
- **Headlines Analysis**: `analysis_type="headlines"` → `AnalysisTypeEnum.HEADLINES`

### Data Sources Metadata

```python
data_sources = {
    "articles_count": len(articles),
    "analyses_count": len(analyses), 
    "positions_count": len(positions_data)
}
```

## Database Integration

- Market summaries are now persistently stored in `market_summaries` table
- Each summary is linked to its analysis session via `session_id`
- Analysis type is tracked to distinguish full vs headline analysis
- Complete LLM response is stored as JSONB in `summary_data` field
- Timestamps track when summaries were generated

## Activity Logging Enhancement

Added new log entry for market summary storage:
```python
self.activity_log.log_analysis_progress(
    "store_market_summary",
    f"Market summary stored in database with ID {db_summary.id}",
    session_id,
    {
        "summary_id": str(db_summary.id),
        "analysis_type": analysis_type,
        "model": llm_model,
        "data_sources": data_sources
    }
)
```

## Error Handling

- Enhanced error logging includes analysis type context
- Database storage failures are logged but don't break the analysis workflow
- Fallback behavior returns error summary if storage fails

## Testing Considerations

- Test both full and headline analysis workflows store summaries
- Verify correct analysis_type enum values are stored
- Confirm data_sources metadata is properly calculated
- Test error handling when database storage fails
- Verify session linkage works correctly

## Future Enhancements

- API endpoints for retrieving stored market summaries
- Historical summary comparison features
- Summary regeneration capabilities
- Bulk summary operations for analysis sessions