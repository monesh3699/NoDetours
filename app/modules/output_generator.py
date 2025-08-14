"""
app/modules/output_generator.py

This module generates detailed travel itineraries and related content based on user preferences.
It handles the creation of itineraries, packing lists, and budget estimates using LLM providers.
"""

import re
import logging
from typing import Dict, List, Any
from api.llm_provider import LLMProvider
from datetime import datetime, timedelta
        
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutputGenerator:
    """
    Generates travel itineraries and recommendations.
    
    This class is responsible for creating detailed travel plans, packing lists,
    and budget estimates based on extracted features and contextual information.
    It uses an LLM provider to generate natural language content.
    
    Attributes:
        llm_provider (LLMProvider): The language model provider for text generation.
    """
    
    def __init__(self, llm_provider: LLMProvider):
        """
        Initialize the OutputGenerator with an LLM provider.
        
        Args:
            llm_provider (LLMProvider): The language model provider for text generation.
        """
        self.llm_provider = llm_provider
        logger.info("Initialized Output generator with provider")
    
    def generate_itinerary(self, 
                          features: Dict[str, Any], 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete travel itinerary based on extracted features and context.
        
        Creates a detailed day-by-day itinerary that incorporates user preferences,
        destination information, weather data, and location context. Also generates
        supplementary information like packing lists and budget estimates.
        
        Args:
            features: Extracted travel preferences including destination, duration,
                     cuisine preferences, place preferences, and transport preferences.
            context: Collected context information including search results, weather data,
                    and location details.
            
        Returns:
            Dictionary containing the generated itinerary, packing list, estimated budget,
            and trip details with the following structure:
            {
                "itinerary": str,  # The main day-by-day travel plan
                "packing_list": str,  # Suggested items to pack
                "estimated_budget": str,  # Budget breakdown
                "trip_details": Dict  # Trip metadata including dates
            }
        """
        logger.info("Generating travel itinerary")
        
        # Prepare context for the prompt
        search_context = self._format_search_context(context.get("search_results", []))
        weather_context = self._format_weather_context(context.get("weather_info", {}))
        location_context = self._format_location_context(context.get("map_info", {}))
        
        # Extract necessary trip details with validation
        destination = features.get('place_to_visit', 'Your Destination')
        
        # Process duration - using new field format
        duration_days = features.get('duration_days', 3)
        if duration_days is None:
            duration_days = 3  # Default to 3 days if not specified
            
        # For compatibility with existing code, simulate start/end dates
        start_date = datetime.now() + timedelta(days=14)  # Default 2 weeks from now
        end_date = start_date + timedelta(days=duration_days)
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # Create trip_dates structure to maintain compatibility
        trip_dates = {
            'start_date': start_date,
            'end_date': end_date,
            'start_date_str': start_date_str,
            'end_date_str': end_date_str,
            'is_specific': True
        }
        
        # Generate specific dates for each day of the itinerary
        daily_dates = self._generate_daily_dates(trip_dates, duration_days)
        
        logger.info(f"Planning trip to {destination} for {duration_days} days")
        logger.info(f"Daily dates: {daily_dates}")
        
        system_prompt = f"""
        You are a personalized travel planning assistant called NoDetours.
        Your goal is to create detailed, personalized travel itineraries based on user preferences,
        external data about destinations, and current context (like weather conditions).
        
        You are a TRUE EXPERT on {destination} and will create a comprehensive travel itinerary.
        
        # {destination} Travel Itinerary for {duration_days} Days
        
        ## Overview
        Welcome to {destination}, known for its [specific unique features]. This itinerary covers a {duration_days}-day trip and includes the best attractions and experiences this destination has to offer.
        
        ## Day 1
        - **Morning**:
          - Visit the Museum of Modern Art, known for its extensive collection of contemporary works
          - Take a walking tour through the Historic District, stopping at the Central Market
        - **Afternoon**:
          - Enjoy lunch at Riverside Café with views of the harbor
          - Explore the National Gardens and the adjacent Botanical Museum
        - **Evening**:
          - Dinner at Giorgio's Restaurant, famous for its local cuisine
          - Attend a show at the Grand Theater or stroll along the illuminated Waterfront Promenade
        
        ## Day 2
        - **Morning**:
          - Visit the Natural History Museum located in the University District
          - Hike through Evergreen Park and enjoy the scenic overlook
        - **Afternoon**:
          - Tour the Metropolitan Cathedral with its famous stained glass windows
          - Visit the City Art Gallery featuring works by local artists
        - **Evening**:
          - Enjoy dinner at Blue Waters Seafood Restaurant
          - Experience the local nightlife at Jazz Club 64
        
        ## Day 3
        - **Morning**:
          - [Activity 1]
          - [Activity 2]
        - **Afternoon**:
          - [Activity 1]
          - [Activity 2]
        - **Evening**:
          - [Activity 1]
          - [Activity 2]
          
        [Continue until you create EXACTLY {duration_days} days in total]
        
        YOU MUST CREATE EXACTLY {duration_days} DAYS IN TOTAL - from Day 1 to Day {duration_days}.
        
        VERY IMPORTANT: Use EXACTLY this format: "## Day X" (where X is 1 through {duration_days}) without any dates or subtitles.
        DO NOT use any special styling, backgrounds, or colors.
        
        At the end, verify that you have created entries for all days from Day 1 through Day {duration_days}.
        
        ## Accommodation
        - **Luxury**: The Grand Hotel {destination} - $300-400 per night, featuring spa facilities and downtown views
        - **Mid-Range**: Parkview Inn - $150-200 per night, centrally located with complimentary breakfast
        - **Budget-Friendly**: Traveler's Lodge - $70-100 per night, clean and basic accommodations near public transportation
        
        ## Transportation
        - The Metro system runs throughout the city with lines 1, 2, and 3 connecting all major attractions
        - City Bus routes 10 and 15 provide service to outer neighborhoods
        - Ride-sharing services like Uber and Lyft are readily available
        - Bicycle rentals available through CityBike at $15 per day
        
        ## Dining Recommendations
        - Harbor View Restaurant - Seafood - Located in the Marina District
        - The Spice Garden - Local Cuisine - Downtown area
        - Pasta Heaven - Italian - Near the Metropolitan Cathedral
        - Green Leaf Café - Vegetarian - University District
        - Night Market Food Stalls - Various cuisines - Open evenings in the Old Quarter
        
        ## Estimated Costs
        - **Accommodation**: $70-400 per night depending on comfort level
        - **Meals**: $15-30 per person for lunch, $25-60 for dinner
        - **Attractions**: Most museums cost $10-20 per person
        - **Local Transportation**: $5-15 per day using public transit
        - **Total Daily Budget**: $100-250 per person per day excluding accommodation
        
        ## Tips
        - The best time to visit the National Gardens is early morning to avoid crowds
        - Most museums are closed on Mondays
        - Carry a light raincoat as afternoon showers are common
        - Look for the "Local's Menu" at restaurants for authentic and affordable options
        - The City Pass ($45) provides entry to 5 major attractions and is worth purchasing
        
        USE THE ABOVE EXAMPLE as a format reference only. You MUST replace ALL content with genuine attractions, restaurants, hotels, and specific details about {destination}.
        
        EXTREMELY IMPORTANT:
        1. NEVER include placeholder text inside square brackets
        2. NEVER use text like "[attraction name]" or "famous museum" - always use the ACTUAL NAMES of real places
        3. EVERY SINGLE attraction, restaurant, museum, park, and hotel MUST be a real place that exists in {destination}
        4. Include the SPECIFIC DATE for each day in the format shown above (YYYY-MM-DD)
        5. Include PRECISE price ranges in local currency for all cost estimates
        6. BE EXTREMELY SPECIFIC and DETAILED about each attraction and location
        
        The user will immediately reject any itinerary containing placeholders or generic descriptions.
        """
        
        user_prompt = f"""
        Create a DETAILED and AUTHENTIC travel itinerary for a trip to {destination} based on the following information:
        
        ## My Travel Details
        Destination: {destination}
        Duration: {duration_days} days
        Place Preferences: {', '.join(features.get('place_preferences', []) or []) or 'General sightseeing, popular attractions'}
        Cuisine Preferences: {', '.join(features.get('cuisine_preferences', []) or []) or 'Local cuisine'}
        Transportation: {features.get('transport_preferences') or 'Public transportation and walking'}
        
        ## Destination Information
        {search_context}
        
        ## Weather Information
        {weather_context}
        
        ## Location Information
        {location_context}
        
        ## EXPERT INSTRUCTIONS
        You are a travel expert specializing in {destination}. I need a HIGHLY SPECIFIC itinerary with REAL places and attractions.
        
        1. Each activity MUST reference a REAL attraction, restaurant, or location in {destination} - use SPECIFIC NAMES
        2. ABSOLUTELY NO PLACEHOLDER TEXT like [attraction name] or [local restaurant]
        3. Use ONLY the format "## Day 1", "## Day 2" WITHOUT any dates or subtitles
        4. I expect detailed morning, afternoon, and evening segments for each day
        5. Each day should have a clear theme or focus area
        6. Include REAL restaurants with their ACTUAL names and cuisine types
        7. Mention SPECIFIC costs in the local currency with realistic price ranges
        8. EXTREMELY IMPORTANT: You MUST create an itinerary for EXACTLY {duration_days} days - no more, no less
        9. You MUST include "## Day 1" through "## Day {duration_days}" - all days must be included
        
        IMPORTANT: 
        - YOU MUST CREATE EXACTLY {duration_days} DAYS OF ITINERARY
        - DO NOT use colored backgrounds, highlight boxes, or any special formatting for days
        - Use ONLY "Day 1", "Day 2", etc. format WITHOUT any dates
        - Use simple, plain text formatting throughout the itinerary
        - Avoid using any Markdown syntax that might create colored boxes or backgrounds
        - DO NOT output the same content twice or include the raw markdown
        - VERIFY that you have created entries for Day 1 through Day {duration_days} before finishing
        
        I will immediately reject any itinerary that doesn't contain exactly {duration_days} days.
        """
        
        try:
            logger.info(f"Generating itinerary for {destination} for {duration_days} days")
            itinerary_text = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            
            logger.info(f"Successfully generated itinerary: {len(itinerary_text)} chars")
            logger.info(f"Itinerary preview: {itinerary_text[:200]}...")
            
            # Store trip details to return along with the itinerary
            # Even though we're not displaying dates in the UI, we'll still include them 
            # in the trip_details for the calendar feature
            trip_details = {
                "place_to_visit": destination,
                "start_date": start_date_str,
                "end_date": end_date_str,
                "duration_days": duration_days,
                "daily_dates": daily_dates
            }
            
            return {
                "itinerary": itinerary_text,
                "packing_list": self.generate_packing_list(features, context),
                "estimated_budget": self.estimate_budget(features, context),
                "trip_details": trip_details
            }
        except Exception as e:
            logger.error(f"Error generating itinerary: {e}", exc_info=True)
            return {
                "itinerary": "I apologize, but I couldn't generate a detailed itinerary. Please try again with more specific information about your trip.",
                "packing_list": "",
                "estimated_budget": "",
                "trip_details": {}
            }
            
    def _parse_trip_dates(self, dates_str: str) -> Dict[str, Any]:
        """
        Parse trip dates from various string formats into structured date information.
        
        Handles multiple date formats including:
        - Standard format "YYYY-MM-DD to YYYY-MM-DD"
        - Month and day ranges like "June 15-20" or "June 15 to June 20"
        - Month-only mentions like "in June"
        
        Args:
            dates_str: String containing date information
            
        Returns:
            Dictionary with the following structure:
            {
                'start_date': datetime object,
                'end_date': datetime object,
                'start_date_str': formatted start date (YYYY-MM-DD),
                'end_date_str': formatted end date (YYYY-MM-DD),
                'is_specific': Boolean indicating if specific dates were found
            }
        """
        
        # Initialize with custom defaults for better demonstration
        # Use a date 3 months in the future for better calendar integration
        future_date = datetime.now() + timedelta(days=90)
        default_start_date = datetime(future_date.year, future_date.month, 15)
        default_duration = 3  # Default duration in days
        
        # Initialize with defaults
        result = {
            'start_date': default_start_date,
            'end_date': default_start_date + timedelta(days=default_duration),
            'start_date_str': '',
            'end_date_str': '',
            'is_specific': False
        }
        
        if not dates_str:
            # Use defaults if no date string provided
            result['start_date_str'] = result['start_date'].strftime('%Y-%m-%d')
            result['end_date_str'] = result['end_date'].strftime('%Y-%m-%d')
            return result
        
        # First, try to parse in standard format "YYYY-MM-DD to YYYY-MM-DD"
        date_range_match = re.match(r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', dates_str)
        if date_range_match:
            try:
                start_date_str = date_range_match.group(1)
                end_date_str = date_range_match.group(2)
                
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                
                # Validate dates are not in the past
                if start_date < datetime.now():
                    # If dates are in the past, move them to next year
                    start_date = datetime(datetime.now().year + 1, start_date.month, start_date.day)
                    end_date = datetime(datetime.now().year + 1, end_date.month, end_date.day)
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                
                result['start_date'] = start_date
                result['end_date'] = end_date
                result['start_date_str'] = start_date_str
                result['end_date_str'] = end_date_str
                result['is_specific'] = True
                
                return result
            except Exception as e:
                logger.error(f"Error parsing standard date range: {e}", exc_info=True)
        
        # Next, try to extract month names
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
            'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'aug': 8, 
            'sep': 9, 'sept': 9, 'oct': 10, 'nov': 11, 'dec': 12
        }
        
        # Check for month and day patterns like "June 15-20" or "June 15 to June 20"
        month_day_range = r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+(\d{1,2})(?:\s*-\s*|\s+to\s+)(?:(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)\s+)?(\d{1,2})'
        
        md_match = re.search(month_day_range, dates_str.lower())
        if md_match:
            try:
                start_month_name = md_match.group(1)
                start_day = int(md_match.group(2))
                end_month_name = md_match.group(3) or start_month_name  # If no end month, use start month
                end_day = int(md_match.group(4))
                
                # Convert month names to numbers
                start_month = months.get(start_month_name, 1)
                end_month = months.get(end_month_name, start_month)
                
                # Determine year (use next year if month is in the past)
                current_year = datetime.now().year
                start_year = current_year
                end_year = current_year
                
                # If the start month is earlier in the year than current month, use next year
                if start_month < datetime.now().month:
                    start_year = current_year + 1
                    end_year = current_year + 1
                
                # Handle year wrap if end month is earlier than start month
                if end_month < start_month:
                    end_year = start_year + 1
                
                # Create datetime objects
                try:
                    start_date = datetime(start_year, start_month, start_day)
                    end_date = datetime(end_year, end_month, end_day)
                    
                    # Format as strings
                    start_date_str = start_date.strftime('%Y-%m-%d')
                    end_date_str = end_date.strftime('%Y-%m-%d')
                    
                    result['start_date'] = start_date
                    result['end_date'] = end_date
                    result['start_date_str'] = start_date_str
                    result['end_date_str'] = end_date_str
                    result['is_specific'] = True
                    
                    return result
                except ValueError:
                    # Invalid date (like February 30) - will fall through to next method
                    pass
            except Exception as e:
                logger.error(f"Error parsing month-day range: {e}", exc_info=True)
        
        # Just month mentioned (like "in June")
        month_only = r'(?:in|during)\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)'
        m_match = re.search(month_only, dates_str.lower())
        if m_match:
            try:
                month_name = m_match.group(1)
                month_num = months.get(month_name, 1)
                
                # Determine year
                current_year = datetime.now().year
                year = current_year
                
                # If the month is earlier in the year than current month, use next year
                if month_num < datetime.now().month:
                    year = current_year + 1
                
                # Use 15th of the month as default start date
                start_date = datetime(year, month_num, 15)
                
                # Extract duration to calculate end date
                duration_match = re.search(r'(\d+)\s+days?', dates_str)
                duration_days = int(duration_match.group(1)) if duration_match else default_duration
                
                end_date = start_date + timedelta(days=duration_days)
                
                # Format as strings
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                
                result['start_date'] = start_date
                result['end_date'] = end_date
                result['start_date_str'] = start_date_str
                result['end_date_str'] = end_date_str
                result['is_specific'] = True
                
                return result
            except Exception as e:
                logger.error(f"Error parsing month-only date: {e}", exc_info=True)
        
        # Use defaults with actual future dates
        result['start_date_str'] = result['start_date'].strftime('%Y-%m-%d')
        result['end_date_str'] = result['end_date'].strftime('%Y-%m-%d')
        return result
        
    def _generate_daily_dates(self, trip_dates: Dict[str, Any], duration_days: int) -> Dict[int, str]:
        """
        Generate a mapping of day numbers to calendar dates for the itinerary.
        
        Creates a dictionary where keys are day numbers (1-based) and values
        are date strings in YYYY-MM-DD format for each day of the trip.
        
        Args:
            trip_dates: Dictionary containing start_date and end_date
            duration_days: Number of days in the itinerary
            
        Returns:
            Dictionary mapping day numbers to date strings:
            {
                1: "2025-05-15",
                2: "2025-05-16",
                ...
            }
        """
        from datetime import datetime, timedelta
        
        daily_dates = {}
        
        try:
            start_date = trip_dates.get('start_date')
            if not start_date:
                # Use reasonable default if no start date
                future_date = datetime.now() + timedelta(days=90)
                start_date = datetime(future_date.year, future_date.month, 15)
            
            # Calculate actual duration based on start/end dates
            if trip_dates.get('end_date'):
                actual_duration = (trip_dates['end_date'] - start_date).days + 1
                duration_days = max(duration_days, actual_duration)  # Use larger of two values
            
            # Generate a date for each day of the itinerary
            for day_num in range(1, duration_days + 1):
                day_date = start_date + timedelta(days=day_num - 1)
                daily_dates[day_num] = day_date.strftime('%Y-%m-%d')
                
            logger.info(f"Generated {len(daily_dates)} daily dates from {daily_dates.get(1)} to {daily_dates.get(duration_days)}")
                
        except Exception as e:
            logger.error(f"Error generating daily dates: {e}", exc_info=True)
            # In case of error, use generic day numbers
            for day_num in range(1, duration_days + 1):
                daily_dates[day_num] = f"Day {day_num}"
                
        return daily_dates
    
    def generate_packing_list(self, 
                             features: Dict[str, Any], 
                             context: Dict[str, Any]) -> str:
        """
        Generate a comprehensive packing list tailored to the trip.
        
        Creates a destination-specific packing list based on weather conditions,
        planned activities, and trip duration. The list is formatted in Markdown
        with clear sections and bullet points.
        
        Args:
            features: Dictionary containing trip features like destination, duration,
                     and activity preferences
            context: Dictionary containing contextual information like weather data
            
        Returns:
            Formatted packing list as a string
        """
        logger.info("Generating packing list")
        
        system_prompt = """
        You are a travel planning assistant. Your task is to create a comprehensive 
        packing list based on the destination, weather conditions, and planned activities.
        Be specific and practical.
        
        Format your response in Markdown with clear sections and bullet points.
        """
        
        # Format weather information
        weather_info = context.get("weather_info", {})
        weather_summary = self._format_weather_context(weather_info)
        
        user_prompt = f"""
        Please create a packing list for a trip to {features.get('place_to_visit', '')}.
        
        Trip details:
        - Duration: {features.get('duration_days', 'Not specified')} days
        - Weather: {weather_summary}
        - Activities: {', '.join(features.get('place_preferences', []) or []) or 'Not specified'}
        - Food interests: {', '.join(features.get('cuisine_preferences', []) or []) or 'Not specified'}
        """
        
        try:
            return self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
        except Exception as e:
            logger.error(f"Error generating packing list: {e}", exc_info=True)
            return "I apologize, but I couldn't generate a packing list. Please try again with more specific information about your trip."
    
    def estimate_budget(self, 
                       features: Dict[str, Any], 
                       context: Dict[str, Any]) -> str:
        """
        Estimate a detailed budget for the trip based on destination and preferences.
        
        Creates a comprehensive budget breakdown including accommodation, transportation,
        food, activities, and miscellaneous expenses with price ranges for different
        spending levels (budget, mid-range, luxury).
        
        Args:
            features: Dictionary containing trip features like destination, duration,
                     and preferences
            context: Dictionary containing contextual information
            
        Returns:
            Formatted budget estimate as a string with sections for different
            expense categories and spending levels
        """
        logger.info("Generating budget estimate")
        
        system_prompt = """
        You are a travel budget estimator. Your task is to provide a reasonable 
        budget estimate based on the destination, accommodation preferences, 
        activities, and travel style. 
        
        Follow this EXACT format for your response:
        
        ### Budget Estimate for [Destination]
        
        #### 1. Accommodation:
        - **Budget Accommodation:** $XX - $XX per night
        - **Mid-Range Accommodation:** $XX - $XX per night
        - **Luxury Accommodation:** $XX - $XX per night
        
        #### 2. Transportation:
        - **Local Transportation:** $XX - $XX
        - **Rental Car (if applicable):** $XX - $XX
        - **Flights (if applicable):** $XX - $XX
        
        #### 3. Food and Dining:
        - **Budget Meals:** $XX - $XX per meal
        - **Mid-Range Restaurants:** $XX - $XX per meal
        - **Fine Dining:** $XX - $XX per meal
        
        #### 4. Activities and Attractions:
        - **Museum/Attraction Entrance Fees:** $XX - $XX per attraction
        - **Tours:** $XX - $XX
        - **Entertainment:** $XX - $XX
        
        #### 5. Miscellaneous Expenses:
        - **Souvenirs:** $XX - $XX
        - **Tips and Gratuities:** $XX - $XX
        
        #### Total Estimated Budget Range:
        - **Low End:** $XXX - $XXX
        - **Mid Range:** $XXX - $XXX
        - **High End:** $XXX - $XXX
        
        *Note: Actual costs may vary based on personal preferences, travel style, and specific requirements.*
        """
        
        user_prompt = f"""
        Please estimate a budget for a trip to {features.get('place_to_visit', '')}.
        
        Trip details:
        - Duration: {features.get('duration_days', 'Not specified')} days
        - Transportation: {features.get('transport_preferences') or 'Public transportation and walking'}
        - Activities: {', '.join(features.get('place_preferences', []) or []) or 'General sightseeing'}
        - Food interests: {', '.join(features.get('cuisine_preferences', []) or []) or 'Local cuisine'}
        
        Make sure your output follows EXACTLY the format specified in the system prompt.
        """
        
        try:
            logger.info("Calling LLM for budget estimation")
            budget = self.llm_provider.generate(
                system_prompt=system_prompt,
                user_prompt=user_prompt
            )
            logger.info(f"Budget generated successfully: {budget[:100]}...")
            return budget
        except Exception as e:
            logger.error(f"Error generating budget estimate: {e}", exc_info=True)
            return "I apologize, but I couldn't generate a budget estimate. Please try again with more specific information about your trip."
    
    def _format_search_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results into a structured string for prompt context.
        
        Organizes search results by feature type and value for use in
        prompt generation, enabling more targeted and relevant responses.
        
        Args:
            search_results: List of dictionaries containing search results
                           with feature types, values, queries, and results
            
        Returns:
            Formatted string with search context information
        """
        if not search_results:
            return "No search results available."
        
        context = []
        
        for query_results in search_results:
            feature_type = query_results.get("feature_type", "")
            feature_value = query_results.get("feature_value", "")
            query = query_results.get("query", "")
            results = query_results.get("results", [])
            
            if results:
                if feature_type and feature_value:
                    context.append(f"Information about {feature_type} '{feature_value}':")
                else:
                    context.append(f"Information about: {query}")
                    
                for num, result in enumerate(results):
                    context.append(f"- Place Name: {result['name']} and Place Description: {result['description']}")
                context.append("")  # Add blank line between query groups
        
        return "\n".join(context)

    def _format_weather_context(self, weather_info: Dict[str, Any]) -> str:
            """
            Format weather information into a structured string for prompt context.
            
            Organizes weather forecast data into a readable format for use in
            travel planning, including temperature ranges and conditions.
            
            Args:
                weather_info: Dictionary containing weather data including location
                            and five-day forecast information
                
            Returns:
                Formatted string with weather information
            """
            if not weather_info:
                return "No weather information available."
            
            location = weather_info.get("location", "")
            forecasts = weather_info.get("five_day_forecast","")
            
            context = []
            
            context.append(f"5-Day Weather forecast for {location}:")
            for forecast in forecasts:
                day = forecast.get("day", "")
                temp_min = forecast.get("min_temp","")
                temp_max = forecast.get("max_temp","")
                description = forecast.get("description", "")
                feels_like = forecast.get("feels_like", "")
                wind_speed = forecast.get("wind_speed")
                
                context.append(f"- Day {day}: Min Temp-{temp_min}, Max Temp-{temp_max}, Feels Like-{feels_like}, Description-{description}, Wind Speed- {wind_speed}")
            context.append("")  # Add blank line
            
            return "\n".join(context)
    
    def _format_location_context(self, location_info: Dict[str, Any]) -> str:
        """
        Format location information into a structured string for prompt context.
        
        Organizes location data including address and nearby places of interest
        (attractions, restaurants, hotels) with their ratings and vicinity.
        
        Args:
            location_info: Dictionary containing location data including
                          formatted address and nearby places categorized by type
            
        Returns:
            Formatted string with location information
        """
        if not location_info:
            return "No location information available."
        
        address = location_info.get("formatted_address", "")
        nearby_places = location_info.get("nearby_places", {})
        
        context = []
        
        if address:
            context.append(f"Location: {address}")
            context.append("")  # Add blank line
        
        # Nearby places
        if nearby_places:
            context.append("Nearby places of interest:")
            
            # Tourist attractions
            attractions = nearby_places.get("tourist_attraction", [])
            if attractions:
                context.append("Tourist Attractions:")
                for place in attractions:
                    name = place.get("name", "")
                    rating = place.get("rating", "")
                    vicinity = place.get("vicinity", "")
                    
                    if name:
                        context.append(f"- {name} ({rating}/5) - {vicinity}")
                context.append("")  # Add blank line
            
            # Restaurants
            restaurants = nearby_places.get("restaurant", [])
            if restaurants:
                context.append("Restaurants:")
                for place in restaurants:
                    name = place.get("name", "")
                    rating = place.get("rating", "")
                    vicinity = place.get("vicinity", "")
                    
                    if name:
                        context.append(f"- {name} ({rating}/5) - {vicinity}")
                context.append("")  # Add blank line
            
            # Hotels
            hotels = nearby_places.get("hotel", [])
            if hotels:
                context.append("Hotels:")
                for place in hotels:
                    name = place.get("name", "")
                    rating = place.get("rating", "")
                    vicinity = place.get("vicinity", "")
                    
                    if name:
                        context.append(f"- {name} ({rating}/5) - {vicinity}")
                context.append("")  # Add blank line
        
        return "\n".join(context)