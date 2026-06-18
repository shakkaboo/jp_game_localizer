import json

import pytest
from app.models import Chunk, Project, SourceFile, SourceLine, Translation
from app.services.export_service import ExportService


class TestExportCsv:
    @staticmethod
    def _seed_project(db_session):
        proj = Project(title="Test Project", genre="RPG", target_tone="formal")
        db_session.add(proj)
        db_session.flush()
        sf = SourceFile(
            project_id=proj.id, original_filename="test.csv",
            file_type="csv", total_lines=3,
        )
        db_session.add(sf)
        db_session.flush()
        chunk = Chunk(
            project_id=proj.id, source_file_id=sf.id,
            chunk_number=1, chunk_title="Scene 1",
        )
        db_session.add(chunk)
        db_session.flush()
        return proj, chunk

    def test_csv_contains_bom(self, db_session):
        proj, chunk = TestExportCsv._seed_project(db_session)
        sl = SourceLine(
            project_id=proj.id, chunk_id=chunk.id,
            source_file_id=chunk.source_file_id,
            line_id="1", character="Hero",
            source_text_ja="こんにちは",
        )
        db_session.add(sl)
        db_session.flush()
        txn = Translation(
            source_line_id=sl.id, project_id=proj.id,
            chunk_id=chunk.id,
            localized_text_en="Hello",
            final_text_en="Hello",
            status="translated",
        )
        db_session.add(txn)
        db_session.commit()

        result = ExportService.export(proj.id, "csv", db_session)
        assert isinstance(result, bytes)
        assert result[:3] == b"\xef\xbb\xbf", "CSV must start with UTF-8 BOM"

    def test_csv_preserves_japanese(self, db_session):
        proj, chunk = TestExportCsv._seed_project(db_session)
        sl = SourceLine(
            project_id=proj.id, chunk_id=chunk.id,
            source_file_id=chunk.source_file_id,
            line_id="1", character="Hero",
            source_text_ja="今日は良い天気ですね",
        )
        db_session.add(sl)
        db_session.flush()
        txn = Translation(
            source_line_id=sl.id, project_id=proj.id,
            chunk_id=chunk.id,
            localized_text_en="It's a nice day today",
            final_text_en="It's a nice day today",
            status="translated",
        )
        db_session.add(txn)
        db_session.commit()

        result = ExportService.export(proj.id, "csv", db_session)
        text = result.decode("utf-8-sig")
        assert "今日は良い天気ですね" in text
        assert "It's a nice day today" in text

    def test_csv_multiple_lines(self, db_session):
        proj, chunk = TestExportCsv._seed_project(db_session)
        lines = [
            ("1", "Hero", "おはよう", "Good morning"),
            ("2", "NPC", "ありがとう", "Thank you"),
            ("3", "Hero", "さようなら", "Goodbye"),
        ]
        for lid, char, ja, en in lines:
            sl = SourceLine(
                project_id=proj.id, chunk_id=chunk.id,
                source_file_id=chunk.source_file_id,
                line_id=lid, character=char,
                source_text_ja=ja,
            )
            db_session.add(sl)
            db_session.flush()
            txn = Translation(
                source_line_id=sl.id, project_id=proj.id,
                chunk_id=chunk.id,
                localized_text_en=en, final_text_en=en,
                status="translated",
            )
            db_session.add(txn)
        db_session.commit()

        result = ExportService.export(proj.id, "csv", db_session)
        text = result.decode("utf-8-sig")
        rows = text.strip().split("\n")
        assert len(rows) == 4  # header + 3 data rows
        assert "おはよう" in rows[1]
        assert "Good morning" in rows[1]
        assert "ありがとう" in rows[2]
        assert "さようなら" in rows[3]

    def test_csv_header(self, db_session):
        proj, chunk = TestExportCsv._seed_project(db_session)
        sl = SourceLine(
            project_id=proj.id, chunk_id=chunk.id,
            source_file_id=chunk.source_file_id,
            line_id="1", character="Hero",
            source_text_ja="テスト",
        )
        db_session.add(sl)
        db_session.flush()
        txn = Translation(
            source_line_id=sl.id, project_id=proj.id,
            chunk_id=chunk.id,
            localized_text_en="Test",
            final_text_en="Test",
            status="translated",
        )
        db_session.add(txn)
        db_session.commit()

        result = ExportService.export(proj.id, "csv", db_session)
        text = result.decode("utf-8-sig")
        header = text.strip().split("\n")[0]
        assert "source_text_ja" in header
        assert "localized_text_en" in header
        assert "final_text_en" in header
        assert "character" in header


class TestExportJson:
    def test_json_unchanged(self, db_session):
        proj, chunk = TestExportCsv._seed_project(db_session)
        sl = SourceLine(
            project_id=proj.id, chunk_id=chunk.id,
            source_file_id=chunk.source_file_id,
            line_id="1", character="Hero",
            source_text_ja="こんにちは",
        )
        db_session.add(sl)
        db_session.flush()
        txn = Translation(
            source_line_id=sl.id, project_id=proj.id,
            chunk_id=chunk.id,
            localized_text_en="Hello",
            final_text_en="Hello",
            status="translated",
        )
        db_session.add(txn)
        db_session.commit()

        result = ExportService.export(proj.id, "json", db_session)
        assert isinstance(result, str)
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["source_text_ja"] == "こんにちは"
        assert data[0]["localized_text_en"] == "Hello"
