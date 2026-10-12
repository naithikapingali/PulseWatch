from monitor.database import init_db, add_endpoint, list_endpoints, save_result, list_results, delete_endpoint


def test_database_lifecycle(tmp_path):
    db=tmp_path/"test.db"
    init_db(db)
    eid=add_endpoint("Test", "https://example.com", db_path=db)
    assert list_endpoints(db)[0]["id"] == eid
    save_result({"endpoint_id":eid,"checked_at":"2026-01-01T00:00:00+00:00",
                 "status_code":200,"response_ms":42.0,"healthy":1,"error":""},db)
    assert len(list_results(db_path=db)) == 1
    delete_endpoint(eid,db)
    assert list_results(db_path=db) == []
