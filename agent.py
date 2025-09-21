import requests
import json
from typing import Dict, List, Any
from config import Config

class TaskPlanningAgent:
    def __init__(self, debug_mode=False):
        self.groq_api_key = Config.GROQ_API_KEY
        self.model = Config.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1"
        self.debug_mode = debug_mode
        
    def web_search(self, query: str, num_results: int = 5) -> str:
        """Perform web search using DuckDuckGo instant answer API"""
        try:
            # Using DuckDuckGo instant answer API (no API key required)
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            # Extract relevant information
            results = []
            
            # Get abstract if available
            if data.get('Abstract'):
                results.append(f"Summary: {data['Abstract']}")
            
            # Get related topics
            if data.get('RelatedTopics'):
                for topic in data['RelatedTopics'][:num_results]:
                    if isinstance(topic, dict) and 'Text' in topic:
                        results.append(topic['Text'])
            
            # Get instant answer if available
            if data.get('Answer'):
                results.append(f"Answer: {data['Answer']}")
                
            return "\n".join(results) if results else f"No specific information found for: {query}"
            
        except Exception as e:
            return f"Search error: {str(e)}"
    
    def get_weather(self, location: str) -> str:
        """Get weather information for a location"""
        try:
            if not Config.OPENWEATHER_API_KEY:
                return "Weather API key not configured"
                
            url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': location,
                'appid': Config.OPENWEATHER_API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                weather_info = {
                    'location': data['name'],
                    'country': data['sys']['country'],
                    'temperature': data['main']['temp'],
                    'description': data['weather'][0]['description'],
                    'humidity': data['main']['humidity'],
                    'wind_speed': data['wind']['speed']
                }
                
                return f"Weather in {weather_info['location']}, {weather_info['country']}: {weather_info['temperature']}°C, {weather_info['description']}, Humidity: {weather_info['humidity']}%, Wind: {weather_info['wind_speed']} m/s"
            else:
                return f"Weather data not available for {location}"
                
        except Exception as e:
            return f"Weather error: {str(e)}"
    
    def create_plan(self, goal: str) -> Dict[str, Any]:
        """Create a detailed plan using LLM with tool calling"""
        
        # Define available tools
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "Search the web for information about places, activities, restaurants, or any topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query"
                            },
                            "num_results": {
                                "type": "integer",
                                "description": "Number of results to return",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather information for a specific location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "City name or location"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]
        
        messages = [
            {
                "role": "system",
                "content": """You are a helpful AI agent that creates detailed, actionable plans from natural language goals. 

When creating plans, you should:
1. Break down the goal into clear, day-by-day steps
2. Use web search to gather current information about places, activities, restaurants, etc.
3. Use weather information when relevant to the plan
4. Structure the output as a clear, organized plan with specific times and locations
5. Include practical details like costs, booking requirements, transportation, etc.

Always use the available tools to gather external information to make your plans more accurate and helpful."""
            },
            {
                "role": "user",
                "content": f"Create a detailed plan for this goal: {goal}"
            }
        ]
        
        try:
            # First call to Groq LLM with tool calling
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": "auto",
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', {}).get('message', response.text)
                
                if 'model_decommissioned' in error_data.get('error', {}).get('code', ''):
                    raise Exception(f"Model '{self.model}' has been decommissioned. Please update config.py with a current model. Error: {error_msg}")
                else:
                    raise Exception(f"Groq API error: {response.status_code} - {error_msg}")
            
            response_data = response.json()
            message = response_data["choices"][0]["message"]
            messages.append(message)
            
            # Process tool calls if any
            if message.get("tool_calls"):
                if self.debug_mode:
                    print(f"🔧 Processing {len(message['tool_calls'])} tool calls...")
                
                for tool_call in message["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    if self.debug_mode:
                        print(f"📞 Calling {function_name} with args: {function_args}")
                    
                    if function_name == "web_search":
                        function_response = self.web_search(
                            query=function_args.get("query"),
                            num_results=function_args.get("num_results", 5)
                        )
                        if self.debug_mode:
                            print(f"🔍 Web search result: {function_response[:100]}...")
                    elif function_name == "get_weather":
                        function_response = self.get_weather(
                            location=function_args.get("location")
                        )
                        if self.debug_mode:
                            print(f"🌤️ Weather result: {function_response}")
                    else:
                        function_response = "Function not available"
                    
                    messages.append({
                        "tool_call_id": tool_call["id"],
                        "role": "tool",
                        "name": function_name,
                        "content": function_response
                    })
                
                # Second call to generate final plan
                final_payload = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": 0.7
                }
                
                final_response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=final_payload
                )
                
                if final_response.status_code != 200:
                    error_data = final_response.json() if final_response.headers.get('content-type', '').startswith('application/json') else {}
                    error_msg = error_data.get('error', {}).get('message', final_response.text)
                    
                    if 'model_decommissioned' in error_data.get('error', {}).get('code', ''):
                        raise Exception(f"Model '{self.model}' has been decommissioned. Please update config.py with a current model. Error: {error_msg}")
                    else:
                        raise Exception(f"Groq API error: {final_response.status_code} - {error_msg}")
                
                final_data = final_response.json()
                plan_content = final_data["choices"][0]["message"]["content"]
            else:
                plan_content = message["content"]
            
            return {
                "goal": goal,
                "plan": plan_content,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "goal": goal,
                "plan": f"Error creating plan: {str(e)}",
                "status": "error"
            }
