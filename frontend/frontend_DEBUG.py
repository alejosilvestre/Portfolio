# =================================================================
# PARCHE PARA frontend.py - VERSIÓN CON DEBUGGING
# =================================================================
# 
# INSTRUCCIONES:
# 1. Abre tu archivo frontend.py
# 2. Busca la línea que dice:
#    # ==========================================
#    # LÓGICA DE BÚSQUEDA
#    # ==========================================
#    if search_clicked:
#
# 3. REEMPLAZA desde "if search_clicked:" hasta "st.rerun()"
#    (líneas 357-413 aproximadamente) con el código de abajo
# =================================================================

# ==========================================
# LÓGICA DE BÚSQUEDA (VERSIÓN CON DEBUGGING)
# ==========================================
if search_clicked:
    st.write("🔍 **DEBUG:** Botón de búsqueda clickeado")  # DEBUG 1
    
    if not query and not location:
        st.warning("⚠️ Por favor, completa al menos el campo de búsqueda o ubicación")
        st.write("⚠️ **DEBUG:** Query y location están vacíos")  # DEBUG 2
    else:
        st.write(f"✅ **DEBUG:** Query = '{query}'")  # DEBUG 3
        st.write(f"✅ **DEBUG:** Location = '{location if location else '(vacío - usará default)'}'")  # DEBUG 4
        
        try:
            with st.spinner("Buscando restaurantes..."):
                st.write("🔄 **DEBUG:** Entrando al spinner...")  # DEBUG 5

                # PREPARACIÓN CORRECTA DE FECHAS
                date_str = ""
                time_str = ""
                
                if st.session_state.selected_date:
                    date_str = st.session_state.selected_date.strftime("%Y-%m-%d")
                
                if st.session_state.selected_time:
                    time_str = st.session_state.selected_time.strftime("%H:%M")

                # Creamos diccionario con todos los inputs obtenidos
                llm_inputs = {
                    "query": query,
                    "location": location,
                    "max_distance": max_distance,
                    "mins": mins,
                    "travel_mode": travel_mode,
                    "price": price_options.get(price, 2),
                    "col_date": date_str,
                    "col_time": time_str,
                    "extras": [e.strip().lower() for e in extra_input.split(",")] if extra_input else []
                }
                
                st.write("📦 **DEBUG:** Inputs preparados para el LLM:")  # DEBUG 6
                st.json(llm_inputs)  # Mostrar los inputs

                # Llamada al LLM
                st.write("🤖 **DEBUG:** Llamando al LLM (Gemini)...")  # DEBUG 7
                llm_response = call_llm(
                    prompt_variables=llm_inputs,
                    parse_json=True
                )
                
                st.write("✅ **DEBUG:** LLM respondió. Tipo de respuesta:", type(llm_response))  # DEBUG 8
                st.write("📄 **DEBUG:** Respuesta del LLM:")  # DEBUG 9
                st.json(llm_response)  # Mostrar la respuesta
                
                # Validar respuesta del LLM
                if not llm_response or not isinstance(llm_response, dict):
                    st.error("❌ **ERROR:** El LLM no devolvió un diccionario válido")
                    st.write(f"Tipo recibido: {type(llm_response)}")
                    st.write(f"Valor: {llm_response}")
                    st.stop()

                # Respuesta a api de Google Places
                st.write("📍 **DEBUG:** Creando payload para Google Places...")  # DEBUG 10
                google_places_payload = PlaceSearchPayload(**llm_response)
                
                st.write("📍 **DEBUG:** Payload creado. Buscando en Google Places...")  # DEBUG 11
                st.json(google_places_payload.dict())  # Mostrar el payload
                
                resultados = places_text_search(google_places_payload)
                
                st.write(f"📊 **DEBUG:** Búsqueda completada. Resultados encontrados: {len(resultados)}")  # DEBUG 12
                
                # Validar que hay resultados
                if not resultados:
                    st.warning("⚠️ No se encontraron restaurantes con esos criterios")
                    st.info("""
                    💡 **Sugerencias:**
                    - Amplía la distancia máxima
                    - Prueba con otro tipo de cocina
                    - Verifica que la ubicación sea correcta
                    - Simplifica la búsqueda (ej: solo "restaurante japonés")
                    """)
                    st.stop()
                
                # Procesamos resultados para la UI filtrando los primeros 3 resultados
                st.write("🔧 **DEBUG:** Procesando resultados para la UI...")  # DEBUG 13
                processed = []
                for i, p in enumerate(resultados):
                    processed.append({
                        "id": i + 1,
                        "name": p.get("name", "Sin nombre"),
                        "area": p.get("neighborhood", "Zona no disponible"),
                        "price": p.get("price_level", "N/A"),
                        "rating": p.get("rating", "N/A")
                    })
                    if i >= 2:
                        break  # Solo los primeros 3

                st.write(f"✅ **DEBUG:** Procesados {len(processed)} restaurantes")  # DEBUG 14
                st.write("🎯 **DEBUG:** Guardando resultados y cambiando a pantalla 2...")  # DEBUG 15
                
                st.session_state.results = processed
                st.session_state.step = 2
                st.rerun()
                
        except KeyError as e:
            st.error(f"❌ **ERROR DE CONFIGURACIÓN:** Falta el campo {str(e)}")
            st.info("El LLM no está devolviendo todos los campos necesarios")
            with st.expander("🐛 Ver respuesta del LLM que causó el error"):
                st.write(llm_response if 'llm_response' in locals() else "No disponible")
                
        except Exception as e:
            st.error(f"❌ **ERROR INESPERADO:** {str(e)}")
            with st.expander("🐛 Ver detalles técnicos del error"):
                import traceback
                st.code(traceback.format_exc())
            
            st.info("""
            📝 **Si ves este error, comparte:**
            1. El mensaje de error completo (copia el texto de arriba)
            2. Los valores de DEBUG que viste antes del error
            3. Esto me ayudará a identificar exactamente dónde falla
            """)


# =================================================================
# FIN DEL PARCHE
# =================================================================
# 
# DESPUÉS DE APLICAR ESTE PARCHE:
# 
# 1. Ejecuta: streamlit run frontend.py
# 
# 2. Haz una búsqueda simple: "restaurante japonés"
# 
# 3. Observa los mensajes de DEBUG que aparecen:
#    - Si ves DEBUG 1-5 pero NO el 6: El problema está en la preparación de inputs
#    - Si ves hasta DEBUG 7 pero NO el 8: El problema está en el LLM
#    - Si ves hasta DEBUG 11 pero NO el 12: El problema está en Google Places
#    - Si ves hasta DEBUG 14 pero NO el 15: El problema está al cambiar de pantalla
# 
# 4. IMPORTANTE: Comparte conmigo:
#    - Hasta qué número de DEBUG llegaste
#    - Qué mensaje de ERROR viste (si apareció alguno)
#    - El contenido de los JSON que se mostraron
# 
# =================================================================

# NOTA SOBRE MODO PRODUCCIÓN:
# Una vez identificado el problema, puedes eliminar todos los
# st.write() que empiezan con "DEBUG" para tener una versión limpia.
