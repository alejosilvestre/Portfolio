from langchain_openai import ChatOpenAI

from langchain.agents import create_agent


llm_openai = ChatOpenAI(model="gpt-5-mini", temperature=0)


def choose_restaurant(restaurants, user_request: str):
    # Recibe un diccionario con los restaurantes y la solicitud del usuario
    # Devuelve el restaurante más adecuado según la solicitud

    system_prompt = (
        f"Tienes la siguiente lista de restaurantes: {restaurants}. "
        f"Basándote en la solicitud del usuario: '{user_request}', "
        "elige el restaurante más adecuado y proporciona su nombre."
    )

    agente1 = create_agent(
        model=llm_openai,
        tools=[],
        system_prompt=system_prompt,
    )

    result = agente1.invoke({"messages": [{"role": "user", "content": user_request}]})
    print(result["messages"][1].content)
