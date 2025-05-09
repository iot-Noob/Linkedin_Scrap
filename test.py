from urllib.parse import urlparse, parse_qs

url = "https://pk.indeed.com/jobs?q=reactjs+developer&l=Lahore..."

# Parse the URL
parsed_url = urlparse(url)

# Extract query parameters into a dictionary
query_params = parse_qs(parsed_url.query)

# Get the value of the 'q' parameter (it's a list)
search_query = query_params.get('q', [''])[0]

print(f"Search term: {search_query}")