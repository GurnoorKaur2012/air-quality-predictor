"""
AIR QUALITY HEALTH ALERT PREDICTOR - Streamlit app
Run from the project folder:   streamlit run app/app.py
(Run `python pipeline.py` first so the outputs/ folder exists.)
"""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from style import ACCENT, ACCENT2, AQI_COLORS, CSS, WARN, background_html

st.set_page_config(page_title="AirAlert India", page_icon="🌫️", layout="wide",
                   initial_sidebar_state="expanded")

ROOT = Path(__file__).resolve().parent.parent
px.defaults.color_discrete_sequence = [ACCENT, WARN, ACCENT2, "#ef476f", "#ffd23f", "#a78bfa", "#3ddc84"]
OUT = ROOT / "outputs"
BUCKETS = list(AQI_COLORS)


# ----------------------------------------------------------------- data loading
@st.cache_data
def load():
    if not (OUT / "results.json").exists():
        return None
    res = json.loads((OUT / "results.json").read_text())
    clean = pd.read_csv(OUT / "clean_data.csv", parse_dates=["Date"])
    feats = pd.read_csv(OUT / "features.csv", parse_dates=["Date"])
    data_file = ROOT / "data" / res["data"]["file"]
    raw = pd.read_csv(data_file, parse_dates=["Date"])
    preds = pd.read_csv(OUT / "test_predictions.csv", parse_dates=["Date"])
    return res, clean, feats, raw, preds


@st.cache_resource
def load_model():
    return joblib.load(OUT / "best_model.pkl")


st.markdown(CSS, unsafe_allow_html=True)
st.markdown(background_html(), unsafe_allow_html=True)

loaded = load()
if loaded is None:
    st.error("No results yet. Open a terminal in the project folder and run:  python pipeline.py")
    st.stop()
R, CLEAN, FEATS, RAW, PREDS = loaded
BUNDLE = load_model()


# ----------------------------------------------------------------- helpers
def html(s):
    """Write raw HTML (lines are stripped so Markdown does not turn them into code blocks)."""
    st.markdown("\n".join(line.strip() for line in s.strip().splitlines()), unsafe_allow_html=True)


def card(title, body, kicker="", right=""):
    html(f"""<div class="glass"><div class="kicker"><span>{kicker}</span><b>{right}</b></div>
         <h4>{title}</h4><p>{body}</p></div>""")


def stat_card(kicker, value, note="", right=""):
    html(f"""<div class="glass"><div class="kicker"><span>{kicker}</span><b>{right}</b></div>
         <div class="big">{value}</div><p>{note}</p></div>""")


def header(num, title, accent, sub):
    html(f"""<div class="stage-tag"><i></i>STAGE {num:02d} OF 12</div>
         <div class="page-title">{title} <span>{accent}</span></div>
         <div class="page-sub">{sub}</div>""")


def style(fig, h=420):
    fig.update_layout(template="plotly_dark", height=h, paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Inter", color="#e3f0ea"),
                      margin=dict(l=10, r=10, t=50, b=10), legend=dict(bgcolor="rgba(0,0,0,0)"),
                      colorway=[ACCENT, WARN, ACCENT2, "#ef476f", "#ffd23f", "#a78bfa"])
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.09)", zerolinecolor="rgba(255,255,255,0.15)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.09)", zerolinecolor="rgba(255,255,255,0.15)")
    return fig


def show(fig, h=420):
    st.plotly_chart(style(fig, h), use_container_width=True, theme=None)


def table(records, **kw):
    st.dataframe(pd.DataFrame(records), use_container_width=True, hide_index=True, **kw)


def aqi_scale():
    rng = ["0-50", "51-100", "101-200", "201-300", "301-400", "401-500"]
    cells = "".join(f'<div style="background:{c}">{b}<small>{r}</small></div>'
                    for (b, c), r in zip(AQI_COLORS.items(), rng))
    html(f'<div class="scale">{cells}</div>')


best = R["conclusion"]
metrics = pd.DataFrame(R["metrics"]["table"])


# ----------------------------------------------------------------- pages
def gauge_svg(p, color):
    """Animated ring gauge (the ring fills up when the page opens)."""
    circ = 2 * np.pi * 88
    return f"""<div class="gauge"><svg width="220" height="220" viewBox="0 0 220 220">
      <circle cx="110" cy="110" r="88" fill="none" stroke="rgba(255,255,255,.12)" stroke-width="14"/>
      <circle class="arc" cx="110" cy="110" r="88" fill="none" stroke="{color}" stroke-width="14"
        stroke-linecap="round" transform="rotate(-90 110 110)" style="--v:{p * circ:.1f}; filter:drop-shadow(0 0 8px {color})"/>
      </svg><div class="center"><div class="pct" style="color:{color}">{p:.0%}</div>
      <div class="cap">POOR-AIR RISK</div><div class="cap">TOMORROW</div></div></div>"""


def spark_svg(values, color):
    """Small line chart of the last 30 days (draws itself in)."""
    v = np.asarray(values, float)
    x = np.linspace(0, 400, len(v))
    y = 55 - (v - v.min()) / max(v.max() - v.min(), 1) * 50
    d = "M" + " L".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, y))
    line201 = 55 - (201 - v.min()) / max(v.max() - v.min(), 1) * 50
    guide = (f'<line x1="0" x2="400" y1="{line201:.1f}" y2="{line201:.1f}" stroke="#ef476f" stroke-dasharray="4 4" opacity=".7"/>'
             if v.min() < 201 < v.max() else "")
    return (f'<svg class="spark" viewBox="0 0 400 60" preserveAspectRatio="none">{guide}'
            f'<path class="line" d="{d}" fill="none" stroke="{color}" stroke-width="2.5"/></svg>')


def risk_color(p):
    return "#3ddc84" if p < .3 else "#ffd23f" if p < .5 else "#ff8c42" if p < .75 else "#ef476f"


def page_home():
    city_now = "Delhi" if "Delhi" in FEATS["City"].values else FEATS["City"].iloc[0]
    cf = FEATS[FEATS["City"] == city_now]
    winter = cf[cf["Date"].dt.month.isin([11, 12, 1]) & cf["AQI"].between(170, 230)]   # a borderline winter day
    day = (winter if len(winter) else cf).iloc[-1]
    risk = float(BUNDLE["model"].predict_proba(day[BUNDLE["features"]].to_frame().T.astype(float))[0, 1])
    col = risk_color(risk)
    last30 = cf[cf["Date"] <= day["Date"]].tail(30)["AQI"]
    html(f"""
    <div class="hero">
      <div>
        <span class="pill"><i></i>AIR STATUS <b>MODEL ONLINE</b></span>
        <div class="headline">BREATHE.<br>PREDICT.<br><span class="glow">PROTECT.</span></div>
        <div class="lead">Forecast tomorrow's smog before it rolls in. A 12-stage predictive
        analytics study across {R['data']['cities']} Indian cities that turns pollution data into
        early health alerts.</div>
      </div>
      <div class="monitor">
        <div class="kicker"><span>AIR HEALTH MONITOR</span><b>● LIVE MODEL</b></div>
        <div style="font-family:'Space Grotesk';font-size:1.5rem;font-weight:600;margin-top:.3rem">{city_now}</div>
        <div class="kicker"><span>DEMO DAY {day['Date'].date()}</span><span>TODAY AQI {day['AQI']:.0f}</span></div>
        {gauge_svg(risk, col)}
        <div class="kicker"><span>LAST 30 DAYS AQI</span><span>— — POOR LINE</span></div>
        {spark_svg(last30.values, ACCENT)}
        <div class="chips"><span class="chip">{best['best_model'].split(' (')[0].upper()}</span>
          <span class="chip">F1 {best['best_f1']:.3f}</span><span class="chip">AUC {best['best_auc']:.3f}</span></div>
      </div>
      <div class="strip">
        <div><div class="ic">◎</div><div class="n">{R['data']['cities']}</div><div class="l">CITIES<br>TRACKED</div></div>
        <div><div class="ic">◷</div><div class="n">{R['data']['rows'] / 1000:.1f}K</div><div class="l">DAYS OF<br>DATA</div></div>
        <div><div class="ic">◆</div><div class="n">{best['best_auc']:.2f}</div><div class="l">BEST<br>AUC-ROC</div></div>
      </div>
    </div>""")
    c1, c2, _ = st.columns([1.1, 1.1, 3])
    c1.button("START JOURNEY  ↗", type="primary", on_click=go_to, args=(1,), use_container_width=True)
    c2.button("LIVE PREDICTOR  +", on_click=go_to, args=(len(PAGES) - 1,), use_container_width=True)
    st.write("")
    a, b, c, d = st.columns(4)
    with a:
        stat_card("STAGES", "12 / 12", "Problem to conclusion, plus two bonus forecasts", "COMPLETE")
    with b:
        stat_card("BEST MODEL", best["best_model"].split(" (")[0], f"F1 score {best['best_f1']:.3f}", "WINNER")
    with c:
        stat_card("POOR-AIR DAYS", f"{R['eda']['poor_share']:.0%}", "of all city-days were AQI 201 or worse", "HISTORY")
    with d:
        nxt = list(R["timeseries"]["future"].items())[0]
        stat_card("NEXT MONTH PM2.5", f"{nxt[1]:.0f}", f"{R['timeseries']['city']} SARIMA forecast for {nxt[0][:7]}", "FORECAST")
    if not R["data"]["real_data"]:
        st.info("Running on the practice copy of the data. Put the real Kaggle city_day.csv in data/ "
                "and run pipeline.py again to see real results.")


def page_problem():
    header(1, "The", "Problem", "Can we warn people one day before the air turns dangerous?")
    html(f"""<div class="glass" style="padding:1.6rem"><div class="kicker"><span>PREDICTION QUESTION</span><b>BINARY</b></div>
         <div class="big" style="font-size:1.7rem">{R['problem']['question']}</div>
         <p style="margin-top:.6rem">{R['problem']['type']}</p></div>""")
    aqi_scale()
    a, b, c = st.columns(3)
    with a: card("Descriptive", R["problem"]["descriptive"], "LOOKS BACK", "WHAT HAPPENED")
    with b: card("Predictive", R["problem"]["predictive"], "LOOKS AHEAD", "THIS PROJECT")
    with c: card("Prescriptive", R["problem"]["prescriptive"], "TAKES ACTION", "WHAT TO DO")
    card("Who uses this?", R["problem"]["industry"], "INDUSTRY", "HEALTHCARE · GOVT")
    st.markdown("#### Ethics, bias and privacy")
    cols = st.columns(len(R["problem"]["ethics"]))
    for i, (col, txt) in enumerate(zip(cols, R["problem"]["ethics"])):
        with col:
            card(txt.split(":")[0], txt.split(":", 1)[1] if ":" in txt else txt, f"RISK {i + 1:02d}")


def page_data():
    d = R["data"]
    header(2, "Data", "Collection", f"Source: {d['source']}.")
    a, b, c, e = st.columns(4)
    a.metric("Rows", f"{d['rows']:,}")
    b.metric("Cities", d["cities"])
    c.metric("Date range", f"{d['date_range'][0][:4]} to {d['date_range'][1][:4]}")
    e.metric("AQI missing", f"{d['aqi_missing_rows']:,}")
    l, r = st.columns([1.2, 1])
    with l:
        miss = pd.Series(d["missing_pct"]).sort_values()
        fig = px.bar(miss, orientation="h", title="Missing values per column (%)",
                     color=miss.values, color_continuous_scale=["#5eead4", "#ffd23f", "#ef476f"])
        fig.update_layout(coloraxis_showscale=False, showlegend=False, yaxis_title="", xaxis_title="%")
        show(fig, 470)
    with r:
        per_city = pd.Series(d["rows_per_city"]).sort_values()
        fig = px.bar(per_city, orientation="h", title="Days of data per city")
        fig.update_layout(showlegend=False, yaxis_title="", xaxis_title="days")
        show(fig, 470)
    st.markdown("#### Problems found")
    a, b, c = st.columns(3)
    worst = max(d["missing_pct"], key=d["missing_pct"].get)
    with a: card("Lots of gaps", f"{worst} is {d['missing_pct'][worst]}% empty. Sensors break and stop reporting.", "PROBLEM 1")
    with b: card("Uneven coverage", "Some cities start in 2015, others only in 2019 or 2020, so cities are not equally represented.", "PROBLEM 2")
    with c: card("Sensor glitches", "Some readings jump to impossible values for one day. These are outliers to treat.", "PROBLEM 3")
    with st.expander("Peek at the raw data"):
        st.dataframe(RAW.head(50), use_container_width=True)
    st.caption(f"Link: {d['url']}  ·  file used: {d['file']}")


def page_preprocess():
    header(3, "Data", "Cleaning", "Fill the gaps, then deal with outliers using the IQR rule and box plots.")
    t1, t2 = st.tabs(["Missing values", "Outliers (IQR + box plot)"])
    with t1:
        mt = pd.DataFrame(R["missing"]["table"]).reset_index().rename(columns={"index": "column"})
        fig = go.Figure([go.Bar(name="Before", x=mt["column"], y=mt["before"], marker_color=WARN),
                         go.Bar(name="After", x=mt["column"], y=mt["after"], marker_color=ACCENT)])
        fig.update_layout(title="Missing values before vs after cleaning", barmode="group")
        show(fig)
        a, b, c = st.columns(3)
        with a: card("1. Interpolate", "Short gaps (up to 7 days) are filled by drawing a line between the days around them, inside each city.", "STEP")
        with b: card("2. City median", "Longer gaps get that city's median, so Delhi is not filled with Chennai's values.", "STEP")
        with c: card("3. Target rows", "AQI is what we predict, so we only fill 2-day gaps and drop the rest. We never invent answers.", "STEP")
    with t2:
        col = st.selectbox("Pollutant", ["PM2.5", "PM10", "NO2", "SO2", "CO", "O3"])
        both = pd.concat([RAW[[col]].assign(stage="Before"), CLEAN[[col]].assign(stage="After")])
        fig = px.box(both, x="stage", y=col, color="stage", points="outliers",
                     color_discrete_map={"Before": WARN, "After": ACCENT},
                     title=f"{col}: box plot before and after capping")
        show(fig, 460)
        table(R["outliers"])
        card("Why cap at 3 x IQR instead of 1.5 x IQR?",
             "Values past 1.5 x IQR are mostly real winter smog days, which are exactly the days we want to predict. "
             "Only the extreme ones past 3 x IQR (per city) look like sensor glitches, so only those are capped.",
             "DECISION")


def page_eda():
    header(4, "Exploratory", "Analysis", "Summary statistics tell us the centre, spread and shape of the data.")
    eda = pd.DataFrame(R["eda"]["table"])
    st.dataframe(eda.style.format(precision=2).background_gradient(cmap="GnBu", subset=["std", "variance"]),
                 use_container_width=True, hide_index=True)
    a, b, c = st.columns(3)
    aq = eda[eda["variable"] == "AQI"].iloc[0]
    with a: stat_card("AQI MEAN vs MEDIAN", f"{aq['mean']:.0f} / {aq['median']:.0f}",
                      "Mean above median means a long right tail of very bad days", "SKEWED")
    with b: stat_card("AQI STD DEVIATION", f"{aq['std']:.0f}", "Typical distance of a day from the average", "SPREAD")
    with c: stat_card("EXTREME DAYS", R["eda"]["z_extreme_days"], "Days with z-score above 3 (very unusual)", "Z-SCORE")
    l, r = st.columns(2)
    with l:
        z = (CLEAN["AQI"] - CLEAN["AQI"].mean()) / CLEAN["AQI"].std()
        fig = px.histogram(z, nbins=70, title="AQI z-scores (lines at -3 and +3)")
        for v in (-3, 3):
            fig.add_vline(v, line_dash="dash", line_color=WARN)
        fig.update_layout(showlegend=False, xaxis_title="z = (AQI - mean) / std")
        show(fig)
    with r:
        cs = pd.DataFrame(R["eda"]["city_stats"]).head(12)
        fig = px.bar(cs, x="City", y="mean", error_y="std", title="Mean AQI ± std, most polluted cities",
                     color="mean", color_continuous_scale=["#5eead4", "#ffd23f", "#ef476f"])
        fig.update_layout(coloraxis_showscale=False)
        show(fig)


def page_viz():
    header(5, "Visual", "Stories", "Five chart types, each answering a different question.")
    cities = st.multiselect("Filter cities (empty = all)", sorted(CLEAN["City"].unique()))
    d = CLEAN[CLEAN["City"].isin(cities)] if cities else CLEAN
    tabs = st.tabs(["Bar", "Histogram", "Pie", "Heatmap", "Scatter"])
    with tabs[0]:
        m = d.groupby("City")["AQI"].mean().sort_values(ascending=False).reset_index()
        fig = px.bar(m, x="City", y="AQI", color="AQI", title="Which city breathes the worst air?",
                     color_continuous_scale=["#3ddc84", "#ffd23f", "#ff8c42", "#ef476f"])
        fig.add_hline(201, line_dash="dash", line_color="#ef476f", annotation_text="Poor starts at 201")
        show(fig, 470)
    with tabs[1]:
        fig = px.histogram(d, x="AQI", nbins=80, color="AQI_Bucket", category_orders={"AQI_Bucket": BUCKETS},
                           color_discrete_map=AQI_COLORS, title="How often does each AQI level happen?")
        show(fig, 470)
    with tabs[2]:
        cnt = d["AQI_Bucket"].value_counts().reindex(BUCKETS).reset_index()
        cnt.columns = ["bucket", "days"]
        fig = px.pie(cnt, names="bucket", values="days", hole=.55, color="bucket",
                     color_discrete_map=AQI_COLORS, title="Share of days in each category")
        show(fig, 470)
    with tabs[3]:
        cols = ["PM2.5", "PM10", "NO", "NO2", "NOx", "NH3", "CO", "SO2", "O3", "Benzene", "Toluene", "Xylene", "AQI"]
        fig = px.imshow(d[cols].corr().round(2), text_auto=True, color_continuous_scale="RdYlGn_r",
                        zmin=-1, zmax=1, title="Which pollutants move together?")
        show(fig, 560)
    with tabs[4]:
        s = d.sample(min(6000, len(d)), random_state=1)
        fig = px.scatter(s, x="PM2.5", y="AQI", color="AQI_Bucket", opacity=.6,
                         category_orders={"AQI_Bucket": BUCKETS}, color_discrete_map=AQI_COLORS,
                         title="PM2.5 drives AQI", hover_data=["City", "Date"])
        show(fig, 470)
    st.markdown("#### Month by month")
    mm = d.assign(month=d["Date"].dt.month).groupby("month")["AQI"].mean().reset_index()
    fig = px.line(mm, x="month", y="AQI", markers=True, title="Winter smog season (Nov to Jan) is clearly visible")
    fig.update_traces(line_color=WARN, line_width=3)
    show(fig, 330)


def page_features():
    f = R["features"]
    header(6, "Feature", "Engineering", "Create smarter inputs, encode text, scale numbers, and keep only the useful ones.")
    a, b, c, d = st.columns(4)
    with a: card("New features", "Yesterday's AQI, 3 and 7 day averages, day-to-day change, PM2.5/PM10 ratio, month as a circle (sin/cos), weekend flag, season.", "CREATE", f"{len(f['engineered'])}")
    with b: card("Encoding", "City and Season are words. One-hot encoding turns each into 0/1 columns the models can read.", "ENCODE", "ONE-HOT")
    with c: card("Scaling", "StandardScaler makes every feature mean 0 and std 1, learned on training data only.", "SCALE", "Z-SCORE")
    with d: card("Selection", f"Dropped near-duplicates ({', '.join(f['redundant_removed']) or 'none'}), then kept the top {len(f['selected'])} by ANOVA F-score.", "SELECT", "SelectKBest")
    l, r = st.columns([1.5, 1])
    with l:
        sc = pd.Series(f["scores"]).sort_values()
        colors = [ACCENT if k in f["selected"] else "rgba(255,255,255,.25)" for k in sc.index]
        fig = go.Figure(go.Bar(x=sc.values, y=sc.index, orientation="h", marker_color=colors))
        fig.update_layout(title="ANOVA F-score (mint = selected)", xaxis_type="log")
        show(fig, 560)
    with r:
        fig = go.Figure(go.Pie(labels=["Not poor tomorrow", "Poor or worse tomorrow"],
                               values=[1 - f["target_share_train"], f["target_share_train"]],
                               hole=.6, marker_colors=[ACCENT, WARN]))
        fig.update_layout(title="Target balance (training data)")
        show(fig, 300)
        card("The target", "For each city and day we look one day ahead: target = 1 if tomorrow's AQI is 201 or more.", "shift(-1)")


def page_models():
    header(7, "Three", "Models", "Same features, same data, three classic classifiers side by side.")
    a, b, c = st.columns(3)
    with a: card("Logistic Regression", "Draws a straight boundary and turns the distance into a probability with the S-shaped sigmoid curve.", "MODEL 01", "LINEAR")
    with b: card("LDA", "Assumes both classes are bell-shaped with the same spread, then finds the best straight line between them.", "MODEL 02", "LINEAR")
    with c: card("QDA", "Like LDA but each class has its own spread, so the boundary can curve. More flexible, easier to overfit.", "MODEL 03", "CURVED")
    m = metrics.melt(id_vars="model", value_vars=["accuracy", "precision", "recall", "f1", "auc"])
    fig = px.bar(m, x="variable", y="value", color="model", barmode="group",
                 title="Test-set scores side by side", range_y=[0, 1.05], text_auto=".3f")
    show(fig, 460)


def page_validation():
    v = R["validation"]
    header(8, "Model", "Validation", v["method"] + ".")
    f = R["features"]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=["Data"], x=[f["train_rows"]], orientation="h", name="Train (past)", marker_color=ACCENT))
    fig.add_trace(go.Bar(y=["Data"], x=[f["test_rows"]], orientation="h", name="Test (future)", marker_color=WARN))
    fig.update_layout(barmode="stack", title=f"Chronological split at {f['split_date']}", height=180)
    show(fig, 180)
    l, r = st.columns([1, 1])
    with l:
        fold = go.Figure()
        for i in range(5):
            fold.add_trace(go.Bar(y=[f"Fold {i + 1}"], x=[i + 1], orientation="h", marker_color=ACCENT, showlegend=i == 0, name="train"))
            fold.add_trace(go.Bar(y=[f"Fold {i + 1}"], x=[1], orientation="h", marker_color=WARN, showlegend=i == 0, name="validate"))
        fold.update_layout(barmode="stack", title="TimeSeriesSplit: always train on the past", xaxis_visible=False)
        show(fold, 330)
    with r:
        rows = []
        for t in v["table"]:
            rows += [{"model": t["model"], "fold": i + 1, "F1": s} for i, s in enumerate(t["fold_f1"])]
        fig = px.line(pd.DataFrame(rows), x="fold", y="F1", color="model", markers=True, title="F1 on each fold")
        show(fig, 330)
    table([{k: t[k] for k in ["model", "cv_f1_mean", "cv_f1_std", "cv_auc_mean", "cv_acc_mean"]} for t in v["table"]])
    card("Why not a random split?", "Air today looks a lot like air yesterday. A random split would put tomorrow's neighbour in the training set and the score would look better than it really is.", "LEAKAGE")


def page_metrics():
    header(9, "Performance", "Metrics", "Accuracy alone lies when only 1 in 5 days is Poor. F1 and AUC tell the real story.")
    st.dataframe(metrics.style.format(precision=3).highlight_max(subset=["accuracy", "precision", "recall", "f1", "auc"], color="#134e4a"),
                 use_container_width=True, hide_index=True)
    l, r = st.columns(2)
    with l:
        name = st.selectbox("Confusion matrix for", list(R["metrics"]["confusion"]))
        cm = np.array(R["metrics"]["confusion"][name])
        fig = px.imshow(cm, text_auto=True, x=["Pred: Not poor", "Pred: Poor+"], y=["Actual: Not poor", "Actual: Poor+"],
                        color_continuous_scale=["#06202a", "#5eead4"], title=name)
        fig.update_layout(coloraxis_showscale=False)
        show(fig, 400)
        tn, fp, fn, tp = cm.ravel()
        st.caption(f"Missed Poor days (false negatives): {fn}. False alarms (false positives): {fp}.")
    with r:
        fig = go.Figure()
        for n, d in R["metrics"]["roc"].items():
            fig.add_trace(go.Scatter(x=d["fpr"], y=d["tpr"], mode="lines", name=n, line_width=3))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random guess", line_dash="dash", line_color="grey"))
        fig.update_layout(title="ROC curves", xaxis_title="False positive rate", yaxis_title="True positive rate")
        show(fig, 470)
    a, b, c = st.columns(3)
    with a: card("Precision", "Of all alerts we raised, how many were really Poor days?", "TP / (TP + FP)")
    with b: card("Recall", "Of all real Poor days, how many did we catch? Matters most for health.", "TP / (TP + FN)")
    with c: card("F1 and AUC", "F1 balances precision and recall. AUC measures ranking quality across every threshold (1.0 = perfect).", "SUMMARY")


def page_tuning():
    header(10, "Hyperparameter", "Tuning", "Grid search tries every combination; random search samples the space.")
    tt = pd.DataFrame(R["tuning"])
    tt["best_params"] = tt["best_params"].astype(str)
    table(tt)
    base = {r["model"]: r["f1"] for r in R["metrics"]["table"]}
    rows = [{"model": "Logistic Regression", "stage": "baseline", "F1": base["Logistic Regression"]},
            {"model": "Logistic Regression", "stage": "grid", "F1": tt.iloc[0]["test_f1"]},
            {"model": "Logistic Regression", "stage": "random", "F1": tt.iloc[1]["test_f1"]},
            {"model": "LDA", "stage": "baseline", "F1": base["LDA"]}, {"model": "LDA", "stage": "grid", "F1": tt.iloc[2]["test_f1"]},
            {"model": "QDA", "stage": "baseline", "F1": base["QDA"]}, {"model": "QDA", "stage": "random", "F1": tt.iloc[3]["test_f1"]}]
    fig = px.bar(pd.DataFrame(rows), x="model", y="F1", color="stage", barmode="group", text_auto=".3f",
                 title="Test F1 before and after tuning")
    fig.update_yaxes(range=[min(r["F1"] for r in rows) - .05, 1])
    show(fig)
    a, b = st.columns(2)
    with a: card("Grid search", "C in {0.001 ... 100} x penalty {L1, L2} x class weight {none, balanced} = 24 combinations, each scored with 5-fold time-series CV.", "EXHAUSTIVE")
    with b: card("Random search", "25 random draws of C from a log scale. Finds good settings faster when the space is large.", "SAMPLED")


def page_fit():
    header(11, "Over &", "Underfitting", "A good model scores well on data it has never seen, not only on data it memorised.")
    ft = pd.DataFrame(R["fit"]["table"])
    ft["model"] = ft["model"].str.split(":").str[0]
    m = ft.melt(id_vars="model", value_vars=["train_f1", "test_f1"])
    fig = px.bar(m, x="model", y="value", color="variable", barmode="group", text_auto=".2f",
                 title="Train vs test F1", color_discrete_map={"train_f1": ACCENT2, "test_f1": WARN})
    fig.update_xaxes(tickangle=0, tickfont_size=10)
    show(fig, 440)
    cols = st.columns(len(ft))
    for col, (_, r) in zip(cols, ft.iterrows()):
        with col:
            card(r["model"], r["what"], "GAP", f"{r['gap']:+.2f}")
    cv = pd.DataFrame(R["fit"]["curve"])
    fig = go.Figure([go.Scatter(x=cv["C"], y=cv["train_f1"], name="Train F1", mode="lines+markers", line_width=3),
                     go.Scatter(x=cv["C"], y=cv["test_f1"], name="Test F1", mode="lines+markers", line_width=3)])
    fig.update_layout(title="Regularization strength vs fit (left = strong regularization)", xaxis_type="log", xaxis_title="C")
    show(fig, 380)


def page_conclusion():
    header(12, "The", "Verdict", "Which model should power the health alert, and what are its limits?")
    html(f"""<div class="glass" style="padding:1.8rem; border-color:rgba(94,234,212,.45)">
         <div class="kicker"><span>WINNING MODEL</span><b>F1 {best['best_f1']:.3f} · AUC {best['best_auc']:.3f}</b></div>
         <div class="big" style="font-size:2.6rem">{best['best_model']}</div>
         <p style="margin-top:.6rem">Best balance of catching Poor days and avoiding false alarms on unseen future data.
         It is also simple, fast and explainable: every coefficient tells you how much a feature pushes the risk up or down.</p></div>""")
    l, r = st.columns([1.2, 1])
    with l:
        rk = pd.DataFrame(best["ranking"])
        fig = px.bar(rk.sort_values("test_f1"), x="test_f1", y="model", orientation="h", color="kind", text_auto=".3f",
                     title="All models ranked by test F1")
        fig.update_xaxes(range=[rk["test_f1"].min() - .05, rk["test_f1"].max() + .02])
        show(fig, 420)
    with r:
        if best["importance"]:
            imp = pd.Series(best["importance"]).head(10).sort_values(key=np.abs)
            fig = go.Figure(go.Bar(x=imp.values, y=imp.index, orientation="h",
                                   marker_color=[WARN if v > 0 else ACCENT for v in imp.values]))
            fig.update_layout(title="What drives tomorrow's risk (orange = raises risk)")
            show(fig, 420)
    st.markdown("#### Limitations")
    cols = st.columns(len(best["limitations"]))
    for i, (c, t) in enumerate(zip(cols, best["limitations"])):
        with c:
            card(f"Limit {i + 1}", t, "CAVEAT")


def page_results():
    C = R["curves"]
    bt = C["best_threshold"]
    html("""<div class="stage-tag"><i></i>RESULTS LAB</div>
         <div class="page-title">The <span>Results</span></div>
         <div class="page-sub">Every curve an examiner looks for: ROC, precision-recall, threshold tuning,
         learning curves, calibration and per-city errors, all computed on the unseen test year.</div>""")
    ap = C["pr"][C["best_name"]]["ap"]
    k = st.columns(5)
    for col, (v, l, n) in zip(k, [(f"{best['best_f1']:.3f}", "F1 SCORE", "at 0.50 threshold"),
                                  (f"{best['best_auc']:.3f}", "AUC-ROC", "ranking quality"),
                                  (f"{ap:.3f}", "AVG PRECISION", "area under PR curve"),
                                  (f"{bt['recall']:.0%}", "POOR DAYS CAUGHT", f"recall at {bt['threshold']:.2f} threshold"),
                                  (f"{len(PREDS):,}", "TEST DAYS", f"from {R['features']['split_date']}")]):
        with col:
            html(f'<div class="glass kpi"><div class="v">{v}</div><div class="l">{l}</div><div class="n">{n}</div></div>')

    tabs = st.tabs(["ROC curve", "Precision-Recall", "Threshold tuner", "Learning curves",
                    "Calibration", "Errors by city"])
    with tabs[0]:
        fig = go.Figure()
        for i, (n, d) in enumerate(R["metrics"]["roc"].items()):
            auc = next(r["auc"] for r in R["metrics"]["table"] if r["model"] == n)
            fig.add_trace(go.Scatter(x=d["fpr"], y=d["tpr"], mode="lines", name=f"{n}  (AUC {auc:.3f})",
                                     line_width=3, fill="tozeroy" if i == 0 else None,
                                     fillcolor="rgba(134,239,172,.10)"))
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Random guess (0.5)",
                                 line=dict(dash="dash", color="grey")))
        fig.update_layout(title="ROC curve: true alarms vs false alarms at every threshold",
                          xaxis_title="False positive rate", yaxis_title="True positive rate (recall)")
        show(fig, 500)
        card("How to read it", "The closer a curve hugs the top-left corner, the better. The shaded area is the AUC "
             "for Logistic Regression: the chance it ranks a random Poor day above a random clean day.", "ROC")
    with tabs[1]:
        fig = go.Figure()
        for n, d in C["pr"].items():
            fig.add_trace(go.Scatter(x=d["recall"], y=d["precision"], mode="lines", line_width=3,
                                     name=f"{n}  (AP {d['ap']:.3f})"))
        base = PREDS["target"].mean()
        fig.add_hline(base, line_dash="dash", line_color="grey", annotation_text=f"No-skill line ({base:.2f})")
        fig.update_layout(title="Precision-Recall curve (better than ROC when Poor days are rare)",
                          xaxis_title="Recall", yaxis_title="Precision", yaxis_range=[0, 1.03])
        show(fig, 500)
    with tabs[2]:
        model_name = C["best_name"]
        l, r = st.columns([1, 1.3])
        with l:
            t = st.slider("Alert threshold (send an alert if risk is above this)", 0.05, 0.95,
                          float(bt["threshold"]), 0.05)
            y, pr = PREDS["target"].values, (PREDS[model_name].values >= t).astype(int)
            tp, fp = int(((pr == 1) & (y == 1)).sum()), int(((pr == 1) & (y == 0)).sum())
            fn, tn = int(((pr == 0) & (y == 1)).sum()), int(((pr == 0) & (y == 0)).sum())
            prec, rec = tp / max(tp + fp, 1), tp / max(tp + fn, 1)
            f1 = 2 * prec * rec / max(prec + rec, 1e-9)
            html(f"""<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:.6rem">
                 <div class="glass kpi" style="padding:.8rem"><div class="v" style="font-size:1.8rem">{prec:.2f}</div><div class="l">PRECISION</div></div>
                 <div class="glass kpi" style="padding:.8rem"><div class="v" style="font-size:1.8rem">{rec:.2f}</div><div class="l">RECALL</div></div>
                 <div class="glass kpi" style="padding:.8rem"><div class="v" style="font-size:1.8rem">{f1:.2f}</div><div class="l">F1</div></div></div>""")
            fig = px.imshow([[tn, fp], [fn, tp]], text_auto=True,
                            x=["Pred: Not poor", "Pred: Poor+"], y=["Actual: Not poor", "Actual: Poor+"],
                            color_continuous_scale=["#0b2219", "#86efac"])
            fig.update_layout(coloraxis_showscale=False, title=f"Confusion matrix at {t:.2f}")
            show(fig, 330)
        with r:
            th = pd.DataFrame(C["threshold"])
            fig = go.Figure()
            for m, w in [("precision", 2), ("recall", 2), ("f1", 5)]:
                fig.add_trace(go.Scatter(x=th["threshold"], y=th[m], name=m.upper() if m == "f1" else m.title(),
                                         mode="lines+markers", line_width=w))
            fig.add_vline(t, line_dash="dash", line_color="white", annotation_text=f"your threshold {t:.2f}")
            fig.update_layout(title="Precision, recall and F1 vs threshold", xaxis_title="Threshold",
                              yaxis_range=[0, 1.02])
            show(fig, 470)
        card("Why this matters for health", f"Lowering the threshold catches more Poor days (higher recall) but sends more "
             f"false alarms. The best F1 is at {bt['threshold']:.2f}, which catches {bt['recall']:.0%} of Poor days. "
             "For a health alert, a slightly lower threshold is often the safer choice.", "DECISION")
    with tabs[3]:
        fig = go.Figure()
        colors = {"Logistic Regression": ACCENT, "LDA": ACCENT2, "QDA": WARN}
        for n, d in C["learning"].items():
            fig.add_trace(go.Scatter(x=d["size"], y=d["train"], name=f"{n} train", mode="lines+markers",
                                     line=dict(color=colors[n], dash="dot", width=2)))
            fig.add_trace(go.Scatter(x=d["size"], y=d["val"], name=f"{n} test", mode="lines+markers",
                                     line=dict(color=colors[n], width=4)))
        fig.update_layout(title="Learning curves: F1 as the model sees more training days",
                          xaxis_title="Training rows (log scale)", xaxis_type="log", yaxis_title="F1",
                          xaxis=dict(tickvals=d["size"], ticktext=[f"{v:,}" for v in d["size"]]))
        show(fig, 500)
        card("How to read it", "Dotted = score on the data it learned from, solid = score on the unseen test year. "
             "Lines that come together mean the model generalises; a gap that stays open means overfitting. "
             "Test F1 keeps rising with more data for the linear models, so more data would still help.", "LEARNING")
    with tabs[4]:
        cal = C["calibration"]
        fig = go.Figure([go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfectly calibrated",
                                    line=dict(dash="dash", color="grey")),
                         go.Scatter(x=cal["pred"], y=cal["actual"], mode="lines+markers", name="Best model",
                                    line=dict(color=ACCENT, width=4), marker_size=10)])
        fig.update_layout(title="Calibration: when the model says 70%, is it right about 70% of the time?",
                          xaxis_title="Predicted probability", yaxis_title="Actual share of Poor days")
        show(fig, 480)
    with tabs[5]:
        t = bt["threshold"]
        p = PREDS.assign(pred=(PREDS[C["best_name"]] >= t).astype(int))
        rows = []
        for c, g in p.groupby("City"):
            tp = ((g.pred == 1) & (g.target == 1)).sum()
            fp = ((g.pred == 1) & (g.target == 0)).sum()
            fn = ((g.pred == 0) & (g.target == 1)).sum()
            rows.append({"City": c, "Poor days": int(g.target.sum()), "Missed": int(fn), "False alarms": int(fp),
                         "Accuracy": (g.pred == g.target).mean()})
        e = pd.DataFrame(rows).sort_values("Poor days", ascending=False)
        fig = go.Figure([go.Bar(x=e["City"], y=e["Poor days"] - e["Missed"], name="Caught", marker_color=ACCENT),
                         go.Bar(x=e["City"], y=e["Missed"], name="Missed", marker_color="#ef476f"),
                         go.Bar(x=e["City"], y=e["False alarms"], name="False alarms", marker_color="#ffd23f")])
        fig.update_layout(barmode="group", title="Per city: Poor days caught, missed, and false alarms")
        show(fig, 460)
        city = st.selectbox("See one city day by day", e["City"].tolist())
        g = p[(p["City"] == city) & (p["Date"] >= "2019-09-01") & (p["Date"] <= "2020-03-31")]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=g["Date"], y=g["AQI_tomorrow"], name="Actual AQI next day",
                                 line=dict(color="#e3f0ea", width=1.5), yaxis="y"))
        fig.add_trace(go.Scatter(x=g["Date"], y=g[C["best_name"]], name="Predicted risk", fill="tozeroy",
                                 line=dict(color=WARN, width=2), fillcolor="rgba(255,140,66,.2)", yaxis="y2"))
        fig.add_hline(201, line_dash="dash", line_color="#ef476f", annotation_text="Poor (201)")
        fig.update_layout(title=f"{city}, winter 2019-20: predicted risk follows the real smog",
                          yaxis=dict(title="AQI"), yaxis2=dict(title="Risk", overlaying="y", side="right", range=[0, 1],
                                                              showgrid=False))
        show(fig, 420)


def page_bonus():
    ts, po = R["timeseries"], R["poisson"]
    html(f"""<div class="stage-tag"><i></i>BONUS</div>
         <div class="page-title">Forecast <span>&amp; Counts</span></div>
         <div class="page-sub">Monthly PM2.5 forecasting for {ts['city']} (SARIMA vs exponential smoothing), and Poisson regression on the number of Poor days per month.</div>""")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=list(ts["actual"]), y=list(ts["actual"].values()), name="Actual", line=dict(color="#e8f4f3", width=2)))
    fig.add_trace(go.Scatter(x=list(ts["sarima_test"]), y=list(ts["sarima_test"].values()), name=f"SARIMA (MAE {ts['mae']['SARIMA']})", line=dict(dash="dash", width=3)))
    fig.add_trace(go.Scatter(x=list(ts["hw_test"]), y=list(ts["hw_test"].values()), name=f"Exp. smoothing (MAE {ts['mae']['Exponential smoothing']})", line=dict(dash="dot", width=3)))
    if "future_lo" in ts:                                   # 95% confidence band
        xs = list(ts["future_lo"]) + list(ts["future_hi"])[::-1]
        ys = list(ts["future_lo"].values()) + list(ts["future_hi"].values())[::-1]
        fig.add_trace(go.Scatter(x=xs, y=ys, fill="toself", fillcolor="rgba(239,71,111,.18)", line_width=0,
                                 name="95% confidence band", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=list(ts["future"]), y=list(ts["future"].values()), name="Next 6 months", line=dict(color="#ef476f", width=4)))
    fig.update_layout(title=f"{ts['city']}: monthly average PM2.5", yaxis_title="µg/m³")
    show(fig, 460)
    l, r = st.columns(2)
    with l:
        rr = pd.Series(po["rate_ratio"]).drop("const")
        fig = px.bar(x=rr.index, y=rr.values, text_auto=".2f", title="Poisson rate ratios (1 = no effect)",
                     color=rr.values > 1, color_discrete_map={True: WARN, False: ACCENT})
        fig.add_hline(1, line_dash="dash")
        fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="x times more Poor days")
        show(fig, 400)
    with r:
        mc = pd.Series(po["monthly_counts"])
        fig = px.bar(x=mc.index.astype(int), y=mc.values, title="Average Poor days per city per month",
                     color=mc.values, color_continuous_scale=["#5eead4", "#ffd23f", "#ef476f"])
        fig.update_layout(coloraxis_showscale=False, xaxis_title="month", yaxis_title="days")
        show(fig, 400)
    card("Reading the rate ratios",
         f"Winter months have {po['rate_ratio']['winter']:.1f}x the Poor days of spring/autumn, the monsoon only "
         f"{po['rate_ratio']['monsoon']:.2f}x. Each year multiplies the count by {po['rate_ratio']['year']:.2f}. "
         f"Deviance/df = {po['deviance_ratio']} (well above 1 means over-dispersion, so a Negative Binomial model is a good next step).",
         "INTERPRETATION")


def risk_gauge(p):
    color = "#3ddc84" if p < .3 else "#ffd23f" if p < .5 else "#ff8c42" if p < .75 else "#ef476f"
    fig = go.Figure(go.Indicator(mode="gauge+number", value=p * 100, number={"suffix": "%", "font": {"size": 54}},
                                 title={"text": "Chance tomorrow is Poor or worse"},
                                 gauge={"axis": {"range": [0, 100]}, "bar": {"color": color},
                                        "bgcolor": "rgba(255,255,255,.04)",
                                        "steps": [{"range": [0, 30], "color": "rgba(61,220,132,.15)"},
                                                  {"range": [30, 50], "color": "rgba(255,210,63,.15)"},
                                                  {"range": [50, 75], "color": "rgba(255,140,66,.15)"},
                                                  {"range": [75, 100], "color": "rgba(239,71,111,.18)"}],
                                        "threshold": {"line": {"color": "white", "width": 3}, "value": 50}}))
    show(fig, 330)
    return color


def alert_card(p, color, city, for_date):
    if p >= .5:
        title, msg = "HEALTH ALERT ISSUED", "Children, elderly and people with asthma or heart disease should avoid outdoor activity tomorrow. Keep windows closed, use N95 masks outdoors, and run air purifiers."
    elif p >= .3:
        title, msg = "WATCH", "Air may worsen. Sensitive groups should keep medicines handy and limit long outdoor exercise."
    else:
        title, msg = "ALL CLEAR", "Tomorrow's air is expected to stay below the Poor level. Normal outdoor activity is fine."
    html(f"""<div class="alert" style="border-color:{color}; background:linear-gradient(120deg,{color}22,transparent)">
         <div class="kicker"><span>{city.upper()} · FOR {for_date:%a %d %b %Y}</span><b style="color:{color}">{p:.0%}</b></div>
         <div class="t" style="color:{color}">{title}</div><p style="color:#cfe7e6; margin-top:.4rem">{msg}</p></div>""")


SEASON = {12: "Winter", 1: "Winter", 2: "Winter", 3: "Summer", 4: "Summer", 5: "Summer",
          6: "Monsoon", 7: "Monsoon", 8: "Monsoon", 9: "Monsoon", 10: "PostMonsoon", 11: "PostMonsoon"}


def live_today():
    """Predict tomorrow from readings the user types in for today's real date."""
    feats = BUNDLE["features"]
    today = pd.Timestamp.today().normalize()
    tomorrow = today + pd.Timedelta(days=1)
    cities = sorted(FEATS["City"].unique())
    l, r = st.columns([1, 1.25])
    with l:
        city = st.selectbox("Your city", cities, index=cities.index("Delhi") if "Delhi" in cities else 0, key="t_city")
        html(f"""<div class="card" style="padding:.7rem 1rem; margin:.3rem 0 .8rem">📅 <b>Today:</b> {today:%A, %d %B %Y}
             &nbsp;→&nbsp; predicting <b>{tomorrow:%d %B}</b><br><span style="color:#9fb8b6; font-size:.85rem">
             Get today's numbers from the <b>Sameer</b> app (CPCB) or <b>aqi.in</b>.</span></div>""")
        # typical values for this city in this month fill in the pollutants you don't type
        cdf = FEATS[FEATS["City"] == city]
        base = cdf[cdf["Date"].dt.month == today.month]
        base = (base if len(base) else cdf).median(numeric_only=True)
        a, b = st.columns(2)
        aqi = a.number_input("AQI today", 0, 999, int(base["AQI"]), key="t_aqi")
        aqi_y = b.number_input("AQI yesterday", 0, 999, int(base["AQI_lag1"]), key="t_aqiy")
        roll7 = a.number_input("Average AQI, last 7 days", 0, 999, int(base["AQI_roll7"]), key="t_r7")
        pm25 = b.number_input("PM2.5 today (µg/m³)", 0.0, 999.0, float(round(base["PM2.5"], 1)), key="t_pm25")
        pm10 = a.number_input("PM10 today (µg/m³)", 0.0, 999.0, float(round(base["PM10"], 1)), key="t_pm10")
        co = b.number_input("CO today (mg/m³)", 0.0, 50.0, float(round(base["CO"], 2)), key="t_co")
    row = base.copy()
    row["AQI"], row["AQI_lag1"], row["AQI_roll7"] = aqi, aqi_y, roll7
    row["AQI_roll3"] = (aqi + aqi_y + roll7) / 3
    row["AQI_change"] = aqi - aqi_y
    row["PM2.5"], row["PM10"], row["CO"] = pm25, pm10, co
    row["PM_ratio"] = pm25 / (pm10 + 1)
    row["month_sin"] = np.sin(2 * np.pi * today.month / 12)
    row["month_cos"] = np.cos(2 * np.pi * today.month / 12)
    row["is_weekend"] = int(today.dayofweek >= 5)
    for f in feats:
        if f.startswith("Season_"):
            row[f] = int(f == "Season_" + SEASON[today.month])
        elif f.startswith("City_"):
            row[f] = int(f == "City_" + city)
    X = row.reindex(feats).fillna(0).to_frame().T.astype(float)
    p = float(BUNDLE["model"].predict_proba(X)[0, 1])
    with r:
        color = risk_gauge(p)
    alert_card(p, color, city, tomorrow)
    st.caption("Pollutants you did not type (NO₂, SO₂, benzene…) use this city's typical value for "
               f"{today:%B}. The model was trained on CPCB data up to 2020, so treat this as a demo, not an official forecast.")


def live_replay():
    feats = BUNDLE["features"]
    test = FEATS[FEATS["Date"] >= pd.Timestamp(R["features"]["split_date"])]
    l, r = st.columns([1, 1.25])
    with l:
        city = st.selectbox("City", sorted(test["City"].unique()), key="r_city",
                            index=sorted(test["City"].unique()).index("Delhi") if "Delhi" in test["City"].values else 0)
        ct = test[test["City"] == city]
        day = st.select_slider("Today's date", options=list(ct["Date"].dt.date), value=list(ct["Date"].dt.date)[len(ct) // 3])
        row = ct[ct["Date"].dt.date == day].iloc[0].copy()
        st.markdown("**What if...**")
        aqi_new = st.slider("Today's AQI", 0, 500, int(row["AQI"]))
        pm_new = st.slider("Today's PM2.5", 0.0, 500.0, float(round(row["PM2.5"], 1)))
        delta = aqi_new - row["AQI"]
        row["AQI"], row["AQI_change"] = aqi_new, row["AQI_change"] + delta
        row["AQI_roll3"] += delta / 3
        row["AQI_roll7"] += delta / 7
        row["PM_ratio"] = pm_new / (row["PM10"] + 1)
        row["PM2.5"] = pm_new
    X = row[feats].to_frame().T.astype(float)
    p = float(BUNDLE["model"].predict_proba(X)[0, 1])
    with r:
        color = risk_gauge(p)
    alert_card(p, color, city, pd.Timestamp(day) + pd.Timedelta(days=1))
    st.write("")
    actual = ct[ct["Date"].dt.date == day].iloc[0]["AQI_tomorrow"]
    a, b, c = st.columns(3)
    a.metric("Today's AQI (used)", f"{aqi_new}")
    b.metric("Actual AQI next day", f"{actual:.0f}", "Poor or worse" if actual >= 201 else "Below Poor",
             delta_color="inverse" if actual >= 201 else "normal")
    c.metric("Model said", "ALERT" if p >= .5 else "No alert")
    hist = ct[(ct["Date"].dt.date <= day)].tail(45)
    fig = px.area(hist, x="Date", y="AQI", title=f"{city}: last 45 days of AQI")
    fig.add_hline(201, line_dash="dash", line_color="#ef476f", annotation_text="Poor")
    fig.update_traces(line_color=ACCENT, fillcolor="rgba(94,234,212,.15)")
    show(fig, 300)


def page_live():
    html("""<div class="stage-tag"><i></i>LIVE</div>
         <div class="page-title">Health Alert <span>Predictor</span></div>
         <div class="page-sub">Type today's readings for your city and get tomorrow's alert, or replay a past day and check the model against what really happened.</div>""")
    t1, t2 = st.tabs(["📅 Today (live readings)", "⏪ Replay a past day"])
    with t1:
        live_today()
    with t2:
        live_replay()


# ----------------------------------------------------------------- navigation
PAGES = [("00", "Home", page_home), ("01", "Problem", page_problem), ("02", "Data", page_data),
         ("03", "Cleaning", page_preprocess), ("04", "EDA", page_eda), ("05", "Visuals", page_viz),
         ("06", "Features", page_features), ("07", "Models", page_models), ("08", "Validation", page_validation),
         ("09", "Metrics", page_metrics), ("10", "Tuning", page_tuning), ("11", "Fit check", page_fit),
         ("12", "Verdict", page_conclusion), ("✦", "Results", page_results), ("★", "Forecast", page_bonus), ("◉", "Predict", page_live)]
LABELS = [f"{n} {t}" for n, t, _ in PAGES]

if "page" not in st.session_state:
    st.session_state.page = 0
    st.session_state.nav = LABELS[0]


def go_to(i):
    st.session_state.page = i
    st.session_state.nav = LABELS[i]


def on_nav():
    st.session_state.page = LABELS.index(st.session_state.nav)


html(f"""<div class="topbar"><div class="brand"><div class="dot"></div>AIRALERT · INDIA</div>
     <div class="stage-count">{st.session_state.page + 1:02d} / {len(PAGES):02d}</div></div>""")
st.radio("Navigate", LABELS, key="nav", horizontal=True, on_change=on_nav, label_visibility="collapsed")
html(f'<div class="progress"><div style="width:{(st.session_state.page + 1) / len(PAGES) * 100:.1f}%"></div></div>')

with st.sidebar:
    html('<div class="brand" style="margin:.4rem 0 1rem"><div class="dot"></div>MISSION DATA</div>')
    st.metric("Cities tracked", R["data"]["cities"])
    st.metric("City-days analysed", f"{R['data']['rows']:,}")
    st.metric("Best model F1", f"{best['best_f1']:.3f}", best["best_model"].split(" (")[0])
    st.metric("Best AUC-ROC", f"{best['best_auc']:.3f}")
    st.button("✦ Open Results Lab", on_click=go_to, args=(13,), use_container_width=True)
    st.markdown("**AQI scale (CPCB)**")
    for b, c in AQI_COLORS.items():
        html(f'<div style="display:flex;gap:.5rem;align-items:center;font-size:.85rem;margin:.15rem 0">'
             f'<span style="width:12px;height:12px;border-radius:3px;background:{c}"></span>{b}</div>')
    if not R["data"]["real_data"]:
        st.caption("Practice data in use")

PAGES[st.session_state.page][2]()

# previous / next buttons at the bottom of every page
st.write("")
i = st.session_state.page
p, _, n = st.columns([1, 3, 1])
if i > 0:
    p.button(f"←  {PAGES[i - 1][1]}", on_click=go_to, args=(i - 1,), use_container_width=True)
if i < len(PAGES) - 1:
    n.button(f"{PAGES[i + 1][1]}  →", on_click=go_to, args=(i + 1,), type="primary", use_container_width=True)
