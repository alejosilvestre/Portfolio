"""
===========================================================
TEST GOOGLE PLACES - Tests para backend/google_places.py
===========================================================

Tests de integración para el módulo de Google Places.
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
import os


class TestPlaceSearchPayload:
    """Tests para PlaceSearchPayload."""

    def test_payload_with_required_fields(self):
        """Verifica creación con campos requeridos."""
        from backend.google_places import PlaceSearchPayload

        payload = PlaceSearchPayload(query="restaurante italiano")

        assert payload.query == "restaurante italiano"
        assert payload.location is None
        assert payload.radius is None

    def test_payload_with_all_fields(self):
        """Verifica creación con todos los campos."""
        from backend.google_places import PlaceSearchPayload

        payload = PlaceSearchPayload(
            query="pizzería",
            location="Madrid centro",
            radius=1500,
            price_level=2,
            extras="terraza wifi",
            max_travel_time=15,
            travel_mode="walking"
        )

        assert payload.query == "pizzería"
        assert payload.location == "Madrid centro"
        assert payload.radius == 1500
        assert payload.price_level == 2
        assert payload.extras == "terraza wifi"
        assert payload.max_travel_time == 15
        assert payload.travel_mode == "walking"

    def test_payload_default_travel_mode(self):
        """Verifica modo de viaje por defecto."""
        from backend.google_places import PlaceSearchPayload

        payload = PlaceSearchPayload(query="restaurante")

        assert payload.travel_mode == "walking"


class TestIsLatLng:
    """Tests para is_lat_lng."""

    def test_valid_lat_lng(self):
        """Verifica detección de coordenadas válidas."""
        from backend.google_places import is_lat_lng

        assert is_lat_lng("40.4168,-3.7038") is True
        assert is_lat_lng("-33.8688,151.2093") is True
        assert is_lat_lng("0,0") is True
        assert is_lat_lng("90.0,-180.0") is True

    def test_invalid_lat_lng(self):
        """Verifica detección de coordenadas inválidas."""
        from backend.google_places import is_lat_lng

        assert is_lat_lng("Madrid") is False
        assert is_lat_lng("40.4168") is False
        assert is_lat_lng("invalid,coords") is False
        assert is_lat_lng("40.4168,-3.7038,extra") is False


class TestGeocodeLocation:
    """Tests para geocode_location."""

    @patch("backend.google_places.requests.get")
    def test_geocode_location_success(self, mock_get, mock_geocode_response):
        """Verifica geocodificación exitosa."""
        from backend.google_places import geocode_location

        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_geocode_response),
            raise_for_status=Mock()
        )

        result = geocode_location("Madrid centro")

        assert result is not None
        assert "40.4168" in result
        assert "-3.7038" in result

    @patch("backend.google_places.requests.get")
    def test_geocode_location_no_results(self, mock_get):
        """Verifica manejo de sin resultados."""
        from backend.google_places import geocode_location

        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"results": [], "status": "ZERO_RESULTS"}),
            raise_for_status=Mock()
        )

        result = geocode_location("Lugar inexistente xyz")

        assert result is None

    @patch("backend.google_places.requests.get")
    def test_geocode_location_handles_error(self, mock_get):
        """Verifica manejo de errores."""
        from backend.google_places import geocode_location

        mock_get.side_effect = Exception("Error de conexión")

        result = geocode_location("Madrid")

        assert result is None


class TestExtractNeighborhood:
    """Tests para extract_neighborhood."""

    def test_extract_neighborhood_from_components(self):
        """Verifica extracción de barrio."""
        from backend.google_places import extract_neighborhood

        components = [
            {"types": ["neighborhood"], "long_name": "Malasaña"},
            {"types": ["locality"], "long_name": "Madrid"}
        ]

        result = extract_neighborhood(components)

        assert result == "Malasaña"

    def test_extract_neighborhood_fallback_to_sublocality(self):
        """Verifica fallback a sublocality."""
        from backend.google_places import extract_neighborhood

        components = [
            {"types": ["sublocality_level_1"], "long_name": "Centro"},
            {"types": ["locality"], "long_name": "Madrid"}
        ]

        result = extract_neighborhood(components)

        assert result == "Centro"

    def test_extract_neighborhood_fallback_to_locality(self):
        """Verifica fallback a locality."""
        from backend.google_places import extract_neighborhood

        components = [
            {"types": ["locality"], "long_name": "Madrid"},
            {"types": ["country"], "long_name": "España"}
        ]

        result = extract_neighborhood(components)

        assert result == "Madrid"

    def test_extract_neighborhood_returns_none(self):
        """Verifica retorno None cuando no hay datos."""
        from backend.google_places import extract_neighborhood

        components = [
            {"types": ["country"], "long_name": "España"}
        ]

        result = extract_neighborhood(components)

        assert result is None


class TestNormalizePlaceDetails:
    """Tests para normalize_place_details."""

    def test_normalize_place_details(self):
        """Verifica normalización de detalles."""
        from backend.google_places import normalize_place_details

        details = {
            "result": {
                "name": "La Trattoria",
                "formatted_address": "Calle Mayor 10, Madrid",
                "formatted_phone_number": "912 345 678",
                "website": "https://latrattoria.com",
                "rating": 4.5,
                "user_ratings_total": 200,
                "price_level": 2,
                "place_id": "ChIJ123",
                "types": ["restaurant", "food"],
                "geometry": {"location": {"lat": 40.4168, "lng": -3.7038}},
                "address_components": [
                    {"types": ["neighborhood"], "long_name": "Centro"}
                ],
                "opening_hours": {"open_now": True}
            }
        }

        result = normalize_place_details(details)

        assert result["name"] == "La Trattoria"
        assert result["address"] == "Calle Mayor 10, Madrid"
        assert result["phone"] == "912 345 678"
        assert result["rating"] == 4.5
        assert result["neighborhood"] == "Centro"


class TestFilterByTravelTime:
    """Tests para filter_by_travel_time."""

    @patch("backend.google_places.requests.get")
    def test_filter_by_travel_time(self, mock_get):
        """Verifica filtrado por tiempo de viaje."""
        from backend.google_places import filter_by_travel_time

        mock_get.return_value = Mock(
            status_code=200,
            json=Mock(return_value={
                "rows": [{
                    "elements": [
                        {"status": "OK", "duration": {"value": 600}},  # 10 min
                        {"status": "OK", "duration": {"value": 1200}},  # 20 min
                        {"status": "OK", "duration": {"value": 300}},  # 5 min
                    ]
                }]
            }),
            raise_for_status=Mock()
        )

        result = filter_by_travel_time(
            origin="40.4168,-3.7038",
            destinations=["40.42,-3.71", "40.43,-3.72", "40.44,-3.73"],
            max_time=15,  # 15 minutos
            mode="walking"
        )

        assert result == [True, False, True]

    def test_filter_by_travel_time_empty_destinations(self):
        """Verifica con lista vacía de destinos."""
        from backend.google_places import filter_by_travel_time

        result = filter_by_travel_time(
            origin="40.4168,-3.7038",
            destinations=[],
            max_time=15
        )

        assert result == []


class TestPlacesTextSearch:
    """Tests para places_text_search."""

    @patch("backend.google_places.requests.post")
    @patch("backend.google_places.geocode_location")
    def test_places_text_search_success(self, mock_geocode, mock_post, mock_places_response):
        """Verifica búsqueda exitosa."""
        from backend.google_places import places_text_search, PlaceSearchPayload

        mock_geocode.return_value = "40.4168,-3.7038"
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_places_response),
            raise_for_status=Mock()
        )

        payload = PlaceSearchPayload(
            query="restaurante italiano",
            location="Madrid"
        )

        result = places_text_search(payload)

        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0]["name"] == "Restaurante El Buen Sabor"

    @patch("backend.google_places.requests.post")
    def test_places_text_search_with_coordinates(self, mock_post, mock_places_response):
        """Verifica búsqueda con coordenadas directas."""
        from backend.google_places import places_text_search, PlaceSearchPayload

        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_places_response),
            raise_for_status=Mock()
        )

        payload = PlaceSearchPayload(
            query="pizzería",
            location="40.4168,-3.7038"
        )

        result = places_text_search(payload)

        assert isinstance(result, list)

    @patch("backend.google_places.requests.post")
    @patch("backend.google_places.geocode_location")
    def test_places_text_search_no_results(self, mock_geocode, mock_post):
        """Verifica búsqueda sin resultados."""
        from backend.google_places import places_text_search, PlaceSearchPayload

        mock_geocode.return_value = "40.4168,-3.7038"
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value={"places": []}),
            raise_for_status=Mock()
        )

        payload = PlaceSearchPayload(
            query="restaurante inexistente xyz",
            location="Madrid"
        )

        result = places_text_search(payload)

        assert result == []

    @patch("backend.google_places.geocode_location")
    def test_places_text_search_geocoding_fails(self, mock_geocode):
        """Verifica error cuando falla geocodificación."""
        from backend.google_places import places_text_search, PlaceSearchPayload

        mock_geocode.return_value = None

        payload = PlaceSearchPayload(
            query="restaurante",
            location="Lugar inexistente xyz"
        )

        with pytest.raises(ValueError) as exc_info:
            places_text_search(payload)

        assert "geocodificar" in str(exc_info.value)

    @patch("backend.google_places.requests.post")
    @patch("backend.google_places.filter_by_travel_time")
    @patch("backend.google_places.geocode_location")
    def test_places_text_search_with_travel_filter(
        self, mock_geocode, mock_filter, mock_post, mock_places_response
    ):
        """Verifica búsqueda con filtro de tiempo de viaje."""
        from backend.google_places import places_text_search, PlaceSearchPayload

        mock_geocode.return_value = "40.4168,-3.7038"
        mock_post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_places_response),
            raise_for_status=Mock()
        )
        mock_filter.return_value = [True]  # Primer resultado pasa el filtro

        payload = PlaceSearchPayload(
            query="restaurante",
            location="Madrid",
            max_travel_time=15
        )

        result = places_text_search(payload)

        assert len(result) == 1
        mock_filter.assert_called_once()


class TestGetPhotoUrl:
    """Tests para get_photo_url."""

    def test_get_photo_url_generates_correct_url(self):
        """Verifica generación de URL correcta."""
        from backend.google_places import get_photo_url

        photo_name = "places/ChIJ123/photos/photo456"

        result = get_photo_url(photo_name)

        assert result is not None
        assert "places.googleapis.com" in result
        assert photo_name in result
        assert "maxWidthPx" in result

    def test_get_photo_url_with_custom_dimensions(self):
        """Verifica URL con dimensiones personalizadas."""
        from backend.google_places import get_photo_url

        photo_name = "places/ChIJ123/photos/photo456"

        result = get_photo_url(photo_name, max_width=800, max_height=600)

        assert "maxWidthPx=800" in result
        assert "maxHeightPx=600" in result

    def test_get_photo_url_returns_none_for_empty(self):
        """Verifica retorno None para nombre vacío."""
        from backend.google_places import get_photo_url

        result = get_photo_url("")

        assert result is None

    def test_get_photo_url_returns_none_for_none(self):
        """Verifica retorno None para None."""
        from backend.google_places import get_photo_url

        result = get_photo_url(None)

        assert result is None
