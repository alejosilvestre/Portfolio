# genai-tfc

## Final master project for Generative AI

### List of files included

- Playground_notebook.ipynb: noteboook donde probar las funciones y workflows

- google*places.sh* contains the curl to generate the restaurants database restaurants.json
- Complete _env.example_ with your env variables. You will need OpenAI key to run main. If you want to generate a new list of restaurants you will need a GOOGLE API key
- frontend.py: Streamlit module that serves as the user interface and forwards user requests to the backend scripts.
- backend_google_places_api.py: Module that implements the logic for interacting with the Google Places API (Text Search). It includes:1.The search payload structure (PlaceSearchPayload),2.The function that performs the actual Text Search request (places_text_search)
- first_input_llm.py: Contains the functions required to generate the structured initial message sent to the LLM. It: 1.Preprocesses the user’s input, 2.Constructs and cleans the JSON-formatted message needed to pass to the Google Places API functions for restaurant search


### How to run the code

- Execute main.py
- Get response on console
- See logs on LangSmith - EU cluster
