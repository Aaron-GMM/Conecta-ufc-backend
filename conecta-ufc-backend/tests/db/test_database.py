import pytest
from unittest.mock import patch, MagicMock
from app.db.database import get_db

def test_get_db_cria_sessao_e_fecha_corretamente():
    # Arrange
    # Fazemos mock do SessionLocal que é chamado dentro de get_db
    with patch("app.db.database.SessionLocal") as mock_session_local:
        mock_db_instance = MagicMock()
        mock_session_local.return_value = mock_db_instance
        
        # Act
        gen = get_db()
        db = next(gen)
        
        # Assert (yields the session)
        assert db == mock_db_instance
        mock_session_local.assert_called_once()
        mock_db_instance.close.assert_not_called()
        
        # Act - fecha o generator para simular o finally
        with pytest.raises(StopIteration):
            next(gen)
            
        # Assert (closes the session)
        mock_db_instance.close.assert_called_once()
