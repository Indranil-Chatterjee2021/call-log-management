from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from db_config import get_db_connection

from .base import CallLogRepository, CallLogRecord, DateRange, MasterRecord


def _normalize_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    s = str(v).strip()
    return s if s else None


class MSSQLRepository(CallLogRepository):
    def close(self) -> None:
        """
        For MSSQL we open and close connections per operation,
        so there's nothing persistent to close here.
        """
        return None

    def master_list(self) -> List[MasterRecord]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT SrNo, MobileNo, Project, TownType, Requester, RDCode, RDName,
                       Town, State, Designation, Name, GSTNo, EmailID, CreatedDate, UpdatedDate
                FROM [dbo].[Master]
                ORDER BY SrNo
                """
            )
            rows = cursor.fetchall()
            records: List[MasterRecord] = []
            for r in rows:
                records.append(
                    {
                        "id": str(r[0]),
                        "SrNo": r[0],
                        "MobileNo": r[1],
                        "Project": r[2],
                        "TownType": r[3],
                        "Requester": r[4],
                        "RDCode": r[5],
                        "RDName": r[6],
                        "Town": r[7],
                        "State": r[8],
                        "Designation": r[9],
                        "Name": r[10],
                        "GSTNo": r[11],
                        "EmailID": r[12],
                        "CreatedDate": r[13],
                        "UpdatedDate": r[14],
                    }
                )
            return records
        finally:
            cursor.close()
            conn.close()

    def master_get(self, record_id: str) -> Optional[MasterRecord]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT SrNo, MobileNo, Project, TownType, Requester, RDCode, RDName,
                       Town, State, Designation, Name, GSTNo, EmailID
                FROM [dbo].[Master]
                WHERE SrNo = ?
                """,
                int(record_id),
            )
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": str(r[0]),
                "SrNo": r[0],
                "MobileNo": r[1],
                "Project": r[2],
                "TownType": r[3],
                "Requester": r[4],
                "RDCode": r[5],
                "RDName": r[6],
                "Town": r[7],
                "State": r[8],
                "Designation": r[9],
                "Name": r[10],
                "GSTNo": r[11],
                "EmailID": r[12],
            }
        finally:
            cursor.close()
            conn.close()

    def master_get_by_mobile(self, mobile_no: str) -> Optional[MasterRecord]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT SrNo, MobileNo, Project, TownType, Requester, RDCode, RDName,
                       Town, State, Designation, Name, GSTNo, EmailID
                FROM [dbo].[Master]
                WHERE MobileNo = ?
                """,
                _normalize_str(mobile_no),
            )
            r = cursor.fetchone()
            if not r:
                return None
            return {
                "id": str(r[0]),
                "SrNo": r[0],
                "MobileNo": r[1],
                "Project": r[2],
                "TownType": r[3],
                "Requester": r[4],
                "RDCode": r[5],
                "RDName": r[6],
                "Town": r[7],
                "State": r[8],
                "Designation": r[9],
                "Name": r[10],
                "GSTNo": r[11],
                "EmailID": r[12],
            }
        finally:
            cursor.close()
            conn.close()

    def master_create(self, record: MasterRecord) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO [dbo].[Master]
                (MobileNo, Project, TownType, Requester, RDCode, RDName, Town, State,
                 Designation, Name, GSTNo, EmailID)
                OUTPUT INSERTED.SrNo
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                _normalize_str(record.get("MobileNo")),
                _normalize_str(record.get("Project")),
                _normalize_str(record.get("TownType")),
                _normalize_str(record.get("Requester")),
                _normalize_str(record.get("RDCode")),
                _normalize_str(record.get("RDName")),
                _normalize_str(record.get("Town")),
                _normalize_str(record.get("State")),
                _normalize_str(record.get("Designation")),
                _normalize_str(record.get("Name")),
                _normalize_str(record.get("GSTNo")),
                _normalize_str(record.get("EmailID")),
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return str(new_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def master_update(self, record_id: str, record: MasterRecord) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE [dbo].[Master]
                SET MobileNo=?, Project=?, TownType=?, Requester=?, RDCode=?, RDName=?,
                    Town=?, State=?, Designation=?, Name=?, GSTNo=?, EmailID=?,
                    UpdatedDate=GETDATE()
                WHERE SrNo=?
                """,
                _normalize_str(record.get("MobileNo")),
                _normalize_str(record.get("Project")),
                _normalize_str(record.get("TownType")),
                _normalize_str(record.get("Requester")),
                _normalize_str(record.get("RDCode")),
                _normalize_str(record.get("RDName")),
                _normalize_str(record.get("Town")),
                _normalize_str(record.get("State")),
                _normalize_str(record.get("Designation")),
                _normalize_str(record.get("Name")),
                _normalize_str(record.get("GSTNo")),
                _normalize_str(record.get("EmailID")),
                int(record_id),
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def master_delete(self, record_id: str) -> None:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM [dbo].[Master] WHERE SrNo = ?", int(record_id))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def master_replace_all(self, records: List[MasterRecord]) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM [dbo].[Master]")
            inserted = 0
            for r in records:
                cursor.execute(
                    """
                    INSERT INTO [dbo].[Master]
                    (MobileNo, Project, TownType, Requester, RDCode, RDName, Town, State,
                     Designation, Name, GSTNo, EmailID)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    _normalize_str(r.get("MobileNo")),
                    _normalize_str(r.get("Project")),
                    _normalize_str(r.get("TownType")),
                    _normalize_str(r.get("Requester")),
                    _normalize_str(r.get("RDCode")),
                    _normalize_str(r.get("RDName")),
                    _normalize_str(r.get("Town")),
                    _normalize_str(r.get("State")),
                    _normalize_str(r.get("Designation")),
                    _normalize_str(r.get("Name")),
                    _normalize_str(r.get("GSTNo")),
                    _normalize_str(r.get("EmailID")),
                )
                inserted += 1
            conn.commit()
            return inserted
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def calllog_create(self, record: CallLogRecord) -> str:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            date_val = record.get("Date")
            if isinstance(date_val, datetime):
                dt = date_val
            else:
                dt = datetime.now()
            cursor.execute(
                """
                INSERT INTO [dbo].[CallLogEntries]
                (Date, MobileNo, Project, Town, Requester, RDCode, RDName,
                 State, Designation, Name, Module, Issue, Solution, SolvedOn, CallOn, Type)
                OUTPUT INSERTED.SrNo
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                dt,
                _normalize_str(record.get("MobileNo")),
                _normalize_str(record.get("Project")),
                _normalize_str(record.get("Town")),
                _normalize_str(record.get("Requester")),
                _normalize_str(record.get("RDCode")),
                _normalize_str(record.get("RDName")),
                _normalize_str(record.get("State")),
                _normalize_str(record.get("Designation")),
                _normalize_str(record.get("Name")),
                _normalize_str(record.get("Module")),
                _normalize_str(record.get("Issue")),
                _normalize_str(record.get("Solution")),
                _normalize_str(record.get("SolvedOn")),
                _normalize_str(record.get("CallOn")),
                _normalize_str(record.get("Type")),
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return str(new_id)
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def calllog_list(self, date_range: DateRange) -> List[CallLogRecord]:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            query = """
                SELECT SrNo, Date, MobileNo, Project, Town, Requester, RDCode, RDName,
                       State, Designation, Name, Module, Issue, Solution, SolvedOn, CallOn, Type
                FROM [dbo].[CallLogEntries]
                WHERE 1=1
            """
            params: List[Any] = []
            if date_range.start:
                query += " AND Date >= ?"
                params.append(date_range.start)
            if date_range.end:
                query += " AND Date <= ?"
                params.append(date_range.end)
            query += " ORDER BY Date DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            out: List[CallLogRecord] = []
            for r in rows:
                out.append(
                    {
                        "id": str(r[0]),
                        "SrNo": r[0],
                        "Date": r[1],
                        "MobileNo": r[2],
                        "Project": r[3],
                        "Town": r[4],
                        "Requester": r[5],
                        "RDCode": r[6],
                        "RDName": r[7],
                        "State": r[8],
                        "Designation": r[9],
                        "Name": r[10],
                        "Module": r[11],
                        "Issue": r[12],
                        "Solution": r[13],
                        "SolvedOn": r[14],
                        "CallOn": r[15],
                        "Type": r[16],
                    }
                )
            return out
        finally:
            cursor.close()
            conn.close()
