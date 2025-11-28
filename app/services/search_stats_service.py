"""
Search Statistics Service for tracking and analyzing search queries
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

from app.models.search_stats import (
    SearchStatCreate,
    SearchStat,
    SearchTrend,
    SearchAnalytics,
    SearchContext
)
from config.settings import settings

logger = logging.getLogger(__name__)


class SearchStatsService:
    """Service for managing search statistics"""
    
    def __init__(self):
        self.client = AsyncIOMotorClient(settings.mongodb_uri)
        self.db = self.client[settings.database_name]
        self.collection = self.db.search_stats
        
    async def record_search(
        self,
        search_data: SearchStatCreate
    ) -> SearchStat:
        """Record a new search query"""
        try:
            # Prepare document for MongoDB
            doc = {
                "_id": str(ObjectId()),
                "query": search_data.query.lower().strip(),  # Normalize query
                "context": search_data.context,
                "results_count": search_data.results_count,
                "brand_id": search_data.brand_id,
                "user_id": search_data.user_id,
                "session_id": search_data.session_id,
                "metadata": search_data.metadata,
                "created_at": datetime.utcnow()
            }
            
            # Insert into MongoDB
            await self.collection.insert_one(doc)
            
            logger.info(f"Recorded search: '{search_data.query}' in context: {search_data.context}")
            
            return SearchStat(**doc)
            
        except Exception as e:
            logger.error(f"Error recording search: {e}")
            raise
    
    async def get_popular_searches(
        self,
        brand_id: Optional[str] = None,
        context: Optional[SearchContext] = None,
        days: int = 30,
        limit: int = 10
    ) -> List[SearchTrend]:
        """Get popular search queries"""
        try:
            # Build match query
            match_query = {
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days)
                }
            }
            
            if brand_id:
                match_query["brand_id"] = brand_id
            if context:
                match_query["context"] = context
            
            # Aggregate popular searches
            pipeline = [
                {"$match": match_query},
                {"$group": {
                    "_id": "$query",
                    "count": {"$sum": 1},
                    "last_searched": {"$max": "$created_at"},
                    "avg_results": {"$avg": "$results_count"},
                    "contexts": {"$addToSet": "$context"}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit},
                {"$project": {
                    "query": "$_id",
                    "count": 1,
                    "last_searched": 1,
                    "avg_results": 1,
                    "contexts": 1,
                    "_id": 0
                }}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            trends = []
            
            async for doc in cursor:
                trends.append(SearchTrend(**doc))
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting popular searches: {e}")
            raise
    
    async def get_recent_searches(
        self,
        brand_id: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20
    ) -> List[SearchStat]:
        """Get recent search queries"""
        try:
            # Build query
            query = {}
            if brand_id:
                query["brand_id"] = brand_id
            if user_id:
                query["user_id"] = user_id
            
            # Get recent searches
            cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
            
            searches = []
            async for doc in cursor:
                searches.append(SearchStat(**doc))
            
            return searches
            
        except Exception as e:
            logger.error(f"Error getting recent searches: {e}")
            raise
    
    async def get_no_results_queries(
        self,
        brand_id: Optional[str] = None,
        days: int = 30,
        limit: int = 20
    ) -> List[str]:
        """Get queries that returned no results"""
        try:
            # Build query
            query = {
                "results_count": 0,
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days)
                }
            }
            
            if brand_id:
                query["brand_id"] = brand_id
            
            # Aggregate queries with no results
            pipeline = [
                {"$match": query},
                {"$group": {
                    "_id": "$query",
                    "count": {"$sum": 1}
                }},
                {"$sort": {"count": -1}},
                {"$limit": limit},
                {"$project": {
                    "query": "$_id",
                    "_id": 0
                }}
            ]
            
            cursor = self.collection.aggregate(pipeline)
            queries = []
            
            async for doc in cursor:
                queries.append(doc["query"])
            
            return queries
            
        except Exception as e:
            logger.error(f"Error getting no results queries: {e}")
            raise
    
    async def get_search_analytics(
        self,
        brand_id: Optional[str] = None,
        days: int = 30
    ) -> SearchAnalytics:
        """Get comprehensive search analytics"""
        try:
            # Build base query
            base_query = {
                "created_at": {
                    "$gte": datetime.utcnow() - timedelta(days=days)
                }
            }
            
            if brand_id:
                base_query["brand_id"] = brand_id
            
            # Get total searches
            total_searches = await self.collection.count_documents(base_query)
            
            # Get unique queries count
            unique_queries_pipeline = [
                {"$match": base_query},
                {"$group": {"_id": "$query"}},
                {"$count": "count"}
            ]
            
            cursor = self.collection.aggregate(unique_queries_pipeline)
            unique_count = 0
            async for doc in cursor:
                unique_count = doc["count"]
            
            # Get popular searches
            popular_searches = await self.get_popular_searches(
                brand_id=brand_id,
                days=days,
                limit=10
            )
            
            # Get recent searches
            recent_searches = await self.get_recent_searches(
                brand_id=brand_id,
                limit=10
            )
            
            # Get no results queries
            no_results_queries = await self.get_no_results_queries(
                brand_id=brand_id,
                days=days
            )
            
            # Get search by context
            context_pipeline = [
                {"$match": base_query},
                {"$group": {
                    "_id": "$context",
                    "count": {"$sum": 1}
                }}
            ]
            
            cursor = self.collection.aggregate(context_pipeline)
            search_by_context = {}
            async for doc in cursor:
                search_by_context[doc["_id"]] = doc["count"]
            
            # Get search by day
            daily_pipeline = [
                {"$match": base_query},
                {"$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1},
                    "unique_queries": {"$addToSet": "$query"}
                }},
                {"$project": {
                    "date": "$_id",
                    "count": 1,
                    "unique_count": {"$size": "$unique_queries"},
                    "_id": 0
                }},
                {"$sort": {"date": 1}}
            ]
            
            cursor = self.collection.aggregate(daily_pipeline)
            search_by_day = []
            async for doc in cursor:
                search_by_day.append(doc)
            
            return SearchAnalytics(
                total_searches=total_searches,
                unique_queries=unique_count,
                popular_searches=popular_searches,
                recent_searches=recent_searches,
                no_results_queries=no_results_queries,
                search_by_context=search_by_context,
                search_by_day=search_by_day
            )
            
        except Exception as e:
            logger.error(f"Error getting search analytics: {e}")
            raise
    
    async def cleanup_old_stats(self, days_to_keep: int = 90):
        """Clean up old search statistics"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            result = await self.collection.delete_many({
                "created_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"Cleaned up {result.deleted_count} old search stats")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old stats: {e}")
            raise


# Create singleton instance
search_stats_service = SearchStatsService()