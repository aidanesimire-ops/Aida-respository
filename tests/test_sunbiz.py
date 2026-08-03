import pandas as pd
import pytest

from waterfront_engine.sunbiz import (
    BulkEntityIndex,
    apply_enrichment,
    parse_detail,
    parse_search_results,
    pick_candidate,
)

SEARCH_HTML = """
<html><body><table><tbody>
  <tr><td><a href="/Inquiry/CorporationSearch/SearchResultDetail?aggregateId=1">BLUE WATER PROPERTIES LLC</a></td>
      <td>L09000011111</td><td>Inactive</td></tr>
  <tr><td><a href="/Inquiry/CorporationSearch/SearchResultDetail?aggregateId=2">BLUE WATER PROPERTIES L.L.C.</a></td>
      <td>L09000022222</td><td>Active</td></tr>
  <tr><td><a href="/Inquiry/CorporationSearch/SearchResultDetail?aggregateId=3">BLUE WATER PROPERTIES OF FL LLC</a></td>
      <td>L09000033333</td><td>Active</td></tr>
</tbody></table></body></html>
"""

DETAIL_HTML = """
<html><body>
 <div class="detailSection"><span>Florida Limited Liability Company</span><span>BLUE WATER PROPERTIES LLC</span></div>
 <div class="detailSection"><span>Filing Information</span>
   <div><label>Document Number</label><span>L09000022222</span></div>
   <div><label>Status</label><span>ACTIVE</span></div>
 </div>
 <div class="detailSection"><span>Principal Address</span><div>1 LAS OLAS BLVD</div><div>FORT LAUDERDALE, FL 33301</div></div>
 <div class="detailSection"><span>Registered Agent Name &amp; Address</span>
   <div>DOE, JANE</div><div>1 LAS OLAS BLVD</div><div>FORT LAUDERDALE, FL 33301</div></div>
 <div class="detailSection"><span>Authorized Person(s) Detail</span>
   <div>Name &amp; Address</div><div>Title MGR</div><div>SMITH, JOHN</div><div>1 LAS OLAS BLVD</div></div>
</body></html>
"""


def test_parse_search_results():
    rows = parse_search_results(SEARCH_HTML)
    assert len(rows) == 3
    assert rows[0]["name"] == "BLUE WATER PROPERTIES LLC"
    assert rows[0]["url"].startswith("https://search.sunbiz.org/")
    assert rows[1]["status"] == "Active"


def test_pick_candidate_prefers_exact_normalized_name():
    rows = parse_search_results(SEARCH_HTML)
    picked = pick_candidate(rows, "BLUE WATER PROPERTIES L.L.C.")
    # normalization strips the dots, so both of the first two rows match exactly;
    # the ACTIVE one wins
    assert picked["doc_number"] == "L09000022222"


def test_pick_candidate_falls_back_to_active_when_no_exact_match():
    rows = parse_search_results(SEARCH_HTML)
    picked = pick_candidate(rows, "SOMETHING ELSE ENTIRELY LLC")
    assert picked["status"] == "Active"


def test_pick_candidate_empty():
    assert pick_candidate([], "ANY LLC") is None


def test_parse_detail_extracts_agent_managers_status():
    parsed = parse_detail(DETAIL_HTML)
    assert "DOE, JANE" in parsed["Registered_Agent"]
    assert "SMITH, JOHN" in parsed["Managers_Members"]
    assert parsed["Sunbiz_DocNumber"] == "L09000022222"
    assert parsed["Sunbiz_Status"] == "ACTIVE"
    assert "1 LAS OLAS BLVD" in parsed["Sunbiz_Principal_Address"]


def test_parse_detail_on_unexpected_markup_is_quiet():
    assert parse_detail("<html><body><p>nothing here</p></body></html>") == {}


# -- bulk index ----------------------------------------------------------
def test_bulk_entity_index_matches_on_normalized_name(tmp_path):
    path = tmp_path / "entities.csv"
    pd.DataFrame(
        {
            "entity_name": ["BLUE WATER PROPERTIES, L.L.C."],
            "managers": ["SMITH, JOHN, MGR"],
            "registered_agent": ["DOE, JANE"],
            "status": ["ACTIVE"],
            "document_number": ["L09000022222"],
        }
    ).to_csv(path, index=False)

    index = BulkEntityIndex(path)
    hit = index.lookup("Blue Water Properties LLC")
    assert hit["Managers_Members"] == "SMITH, JOHN, MGR"
    assert hit["Sunbiz_Status"] == "ACTIVE"
    assert index.lookup("UNKNOWN HOLDINGS LLC")["Sunbiz_Entity"] == "NO MATCH"


def test_bulk_entity_index_rejects_bad_name_column(tmp_path):
    path = tmp_path / "entities.csv"
    pd.DataFrame({"whatever": ["X"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="no column"):
        BulkEntityIndex(path)


# -- application ---------------------------------------------------------
class StubResolver:
    def __init__(self):
        self.calls = []

    def lookup(self, name):
        self.calls.append(name)
        return {"Sunbiz_Entity": name, "Managers_Members": "A MANAGER"}


def test_apply_enrichment_only_touches_masked_rows_once_per_owner():
    df = pd.DataFrame(
        {
            "OWNERNME1": ["ACME LLC", "ACME LLC", "SMITH JOHN"],
            "Entity_YN": ["Y", "Y", "N"],
        }
    )
    resolver = StubResolver()
    out = apply_enrichment(df, resolver, mask=df["Entity_YN"] == "Y", owner_field="OWNERNME1")

    assert resolver.calls == ["ACME LLC"], "one lookup per distinct owner"
    assert list(out["Managers_Members"]) == ["A MANAGER", "A MANAGER", ""]
    assert "Registered_Agent" in out.columns  # columns exist even when unfilled


def test_apply_enrichment_without_owner_field_is_a_no_op():
    df = pd.DataFrame({"OTHER": ["x"]})
    out = apply_enrichment(df, StubResolver(), owner_field="OWNERNME1")
    assert list(out["OTHER"]) == ["x"]
    assert (out["Managers_Members"] == "").all()
