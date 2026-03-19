# Original Prompt Verbatim

Saved from the contributor post as provided. Typos are preserved on purpose.

---

Google Maps API  
Part 1: Fetch Top 20 Restaurants in a Rectangular Area  
Using the Google Maps Places API, write a function that retrieves the top 20 restaurants within a specified rectangular bounding box. The function should accept two latitude/longitude pairs that define the bounding box and return a list of restaurants, sorted by rating.

Part 2: Filter by Cuisine Type & Price Summary  
Extend your solution to allow filtering by cuisine type (e.g., "Mexican," "Italian," "Japanese") and compute the average price level for each cuisine type found in the results. Google's price levels range from 0 (Free) to 4 (Very Expensive).

Example Input:

fetch_top_restaurants( 
bounds=((37.7749, -122.4194), (37.8049, -122.3894)),
cuisine_types=["Mexican", "Italian", "Japanese"] 
) 
Example Output:

{ 
"Mexican": {"count": 5, "avg_price_level": 2.4}, 
"Italian": {"count": 6, "avg_price_level": 3.0}, 
"Japanese": {"count": 4, "avg_price_level": 2.8} 
} 
Follow-Up Questions:

How would you handle API rate limits efficiently?
What if the API doesn't provide a "cuisine" field directly? How could you infer it? 3. How would you modify the function to work in a paginated manner for large areas?
LLM API  
Here at Scale Al, we work with crowdworkers to generate high-quality training data called "tasks" to improve language models. These "tasks" are stored in Mongo as a set of JSON blobs. You can think of each task as a JSON blob with a few fields like:

{
  "customer": "...",
  "project_id": "...",
  "category": "...",
  "prompt": "...",
  "response": "..."
}
customer, project id, category, and a prompt-response pair. The prompt is an example of a question a user would ask an LLM, and the response is how the LLM should respond.

We want to create a way for our internal operations team to take these tasks and gauge the "quality" of the task using an external LLM. Operators on our internal team can select up to 5000 tasks and send them to an LLM to check how well the response answers the question, grammar, style, etc. Tasks flagged for poor quality may then be manually reviewed.

We want to enable operators to:

See all tasks in a webapp and filter them down to at most 5000 tasks they want to review.
Kick-off a job to take those tasks and send them to an external LLM to be reviewed for quality. We should be able to handle instability with that model provider and applicable rate limits.
Once the job is complete, we will email them a link to download a CSV of the results using an existing email service.
Places API  
Joey is planning a multi-week ski trip, where he will be driving between multiple resorts. As he is lazy, he would like to drive as little as possible. He is having trouble determining the optimal route between resorts, and he would like to build an application that uses the Google Maps Platform to simplify this process for this trip as well as his future trips. He will be sleeping in the resorts’ parking lots, so you do not need to worry about transportation to anywhere besides the ski resorts.

Part 1
The first step to building this application is to use the Places API (New APIs) to convert the resort names, as well as Joey’s home address, into place IDs, which can then be used in the rest of the Maps Platform APIs. You should only use the new API for this part; you can ignore the old one. https://developers.google.com/maps/documentation/places/web-service/overview

Part 2
Now that we’ve identified the place IDs of the locations Joey needs to travel to along his trip, we need to determine what the optimal route is to visit these locations to minimize travel time. We should use the Routes API to determine the time it takes to drive between each pair of these locations. https://developers.google.com/maps/documentation/routes

Part 3
Now that we have the distances between the various locations, we would like to determine the best sequence of resorts to visit that minimizes the total travel time. Remember that this is a round trip, so Joey is starting and ending at his home address.
