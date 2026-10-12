"""Streamlit UI: Website & API Health Monitor."""
import pandas as pd
import plotly.express as px
import streamlit as st
from monitor.database import (init_db, list_endpoints, list_results, add_endpoint,
                              update_endpoint, delete_endpoint)
from monitor.service import run_checks
from monitor.seed import seed

st.set_page_config(page_title="PulseWatch | Health Monitor", page_icon="💚", layout="wide")
init_db()
st.markdown("""<style>
.block-container{padding-top:1.5rem;max-width:1450px}
.hero{background:linear-gradient(110deg,#123f48,#182b4a);padding:25px 30px;border-radius:20px;
      border:1px solid #2d5260;margin-bottom:18px}
.hero h1{color:#e6fffa;margin:0;font-size:2.2rem}
.hero p{color:#b5d7dc;margin:8px 0 0}
[data-testid="stMetric"]{background:#172337;padding:16px;border-radius:14px;border:1px solid #304056}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>◉ PulseWatch</h1><p>Website & API Health Monitor · Python Portfolio Project</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Controls")
    page = st.radio("Navigate", ["Overview", "Manage Endpoints", "History & Export"], label_visibility="collapsed")
    st.divider()
    if st.button("▶ Run checks now", use_container_width=True, type="primary"):
        with st.spinner("Checking enabled endpoints..."):
            outcomes = run_checks()
        st.success(f"Completed {len(outcomes)} checks")
        st.rerun()
    if st.button("＋ Add sample endpoints", use_container_width=True):
        count = seed()
        st.info(f"Added {count} samples (only when list is empty).")
        st.rerun()
    st.caption("Automatic monitoring: run `python -m monitor.worker --interval 60` in another terminal. Refresh this page to view updates.")

endpoints = list_endpoints()
results = list_results()

if page == "Overview":
    st.subheader("System overview")
    latest = {}
    for r in results:
        latest.setdefault(r["endpoint_id"], r)
    enabled = [e for e in endpoints if e["enabled"]]
    healthy_count = sum(latest.get(e["id"], {}).get("healthy", 0) for e in enabled)
    checked_count = sum(e["id"] in latest for e in enabled)
    recent = [r for r in results if r["endpoint_id"] in {e["id"] for e in enabled}]
    uptime = sum(r["healthy"] for r in recent)/len(recent)*100 if recent else 0
    avg_ms = sum(r["response_ms"] for r in recent)/len(recent) if recent else 0
    a,b,c,d = st.columns(4)
    a.metric("Monitored", len(enabled))
    b.metric("Healthy (latest)", f"{healthy_count}/{checked_count}")
    c.metric("Historical success rate", f"{uptime:.1f}%" if recent else "—")
    d.metric("Average latency", f"{avg_ms:.0f} ms" if recent else "—")
    st.caption("Metrics reflect stored checks only. Historical success rate is based on the most recent 2,000 records.")
    if not endpoints:
        st.info("No endpoints yet. Select 'Add sample endpoints' or go to Manage Endpoints.")
    else:
        st.subheader("Endpoint status")
        cards=[]
        for e in endpoints:
            last=latest.get(e["id"])
            status=("Paused" if not e["enabled"] else "Not checked" if not last
                    else "Healthy" if last["healthy"] else "Unhealthy")
            cards.append({"Name":e["name"], "Status":status,"URL":e["url"],
                          "HTTP":last["status_code"] if last else None,
                          "Latency (ms)":last["response_ms"] if last else None,
                          "Last checked (UTC)":last["checked_at"] if last else "—"})
        st.dataframe(pd.DataFrame(cards), hide_index=True, use_container_width=True)
    if results:
        df=pd.DataFrame(results)
        df["checked_at"]=pd.to_datetime(df["checked_at"], utc=True)
        df=df.sort_values("checked_at")
        st.subheader("Latency trend")
        fig=px.line(df, x="checked_at", y="response_ms", color="name", markers=True,
                    labels={"checked_at":"Time (UTC)","response_ms":"Response time (ms)","name":"Endpoint"})
        fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", height=360)
        st.plotly_chart(fig, use_container_width=True)
        failures=[r for r in results if not r["healthy"]]
        if failures:
            st.subheader("Recent failures")
            st.dataframe(pd.DataFrame(failures[:15])[["checked_at","name","status_code","error"]],
                         hide_index=True, use_container_width=True)

elif page == "Manage Endpoints":
    st.subheader("Add a new endpoint")
    with st.form("add_endpoint", clear_on_submit=True):
        name=st.text_input("Friendly name", placeholder="My Production API")
        url=st.text_input("HTTP(S) URL", placeholder="https://example.com/health")
        x,y,z=st.columns(3)
        method=x.selectbox("Method", ["GET","HEAD"])
        status=y.number_input("Expected HTTP status", min_value=100,max_value=599,value=200)
        contains=z.text_input("Expected response text (optional)")
        submitted=st.form_submit_button("Add endpoint", type="primary")
        if submitted:
            try:
                add_endpoint(name,url,method,status,contains)
                st.success("Endpoint added")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.divider()
    st.subheader("Existing endpoints")
    if not endpoints:
        st.info("No endpoints configured")
    for e in endpoints:
        with st.expander(f"{'🟢' if e['enabled'] else '⚪'} {e['name']} · {e['url']}"):
            with st.form(f"edit_{e['id']}"):
                ename=st.text_input("Name",value=e["name"])
                eurl=st.text_input("URL",value=e["url"])
                c1,c2=st.columns(2)
                emethod=c1.selectbox("Method",["GET","HEAD"],index=["GET","HEAD"].index(e["method"]))
                estatus=c2.number_input("Expected status",100,599,int(e["expected_status"]))
                etext=st.text_input("Expected response text",value=e["contains_text"])
                enabled=st.checkbox("Monitoring enabled",value=bool(e["enabled"]))
                save=st.form_submit_button("Save changes")
                if save:
                    try:
                        update_endpoint(e["id"],ename,eurl,emethod,estatus,etext,enabled)
                        st.success("Saved")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))
            if st.button("Delete endpoint and its history",key=f"delete_{e['id']}"):
                delete_endpoint(e["id"])
                st.rerun()

else:
    st.subheader("History & CSV export")
    if not results:
        st.info("Run a health check to create history.")
    else:
        df=pd.DataFrame(results)
        options=["All"]+sorted(df["name"].unique().tolist())
        chosen=st.selectbox("Filter by endpoint",options)
        if chosen!="All":
            df=df[df["name"]==chosen]
        df["Result"]=df["healthy"].map({1:"PASS",0:"FAIL"})
        st.dataframe(df[["checked_at","name","url","status_code","response_ms","Result","error"]],
                     use_container_width=True,hide_index=True)
        st.download_button("⬇ Download CSV report", df.to_csv(index=False).encode("utf-8"),
                           file_name="pulsewatch_health_report.csv",mime="text/csv")
