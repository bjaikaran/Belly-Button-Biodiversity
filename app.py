import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, MetaData, inspect, select
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from flask import Flask, jsonify, render_template, request, flash, redirect

path = "DataSets/belly_button_biodiversity.sqlite"
engine = create_engine("sqlite:///"+path, echo=False)
Base = automap_base()
Base.prepare(engine, reflect=True)
meta = Base.metadata
meta.reflect(bind=engine)
# Binding the SQLITE engine to the current Session (locking file)
session = Session(bind=engine).connection_callable
inspector = inspect(engine)

# Gathering Database Information
OTU = Base.classes.otu
SAMPLES = Base.classes.samples
META = Base.classes.samples_metadata

OTU_COLS = []
columns = inspector.get_columns("otu")
for col in columns:
    OTU_COLS.append(col["name"])

SAMPLE_COLS = []
columns = inspector.get_columns("samples")
for col in columns:
    SAMPLE_COLS.append(col["name"])

META_COLS = []
columns = inspector.get_columns("samples_metadata")
for col in columns:
    META_COLS.append(col["name"])

OTU_df = pd.read_sql("SELECT * FROM otu",
                     con=engine,
                     columns=[OTU_COLS],
                     index_col="otu_id")

SAMPLES_df = pd.read_sql("SELECT * FROM samples",
                         con=engine,
                         columns=[SAMPLE_COLS],
                         index_col="otu_id")

META_ALL_df = pd.read_sql("SELECT * FROM samples_metadata",
                          con=engine,
                          columns=[META_COLS])

# META_df SQL statement:
META_sql = "SELECT AGE, \
                UPPER(BBTYPE) as BBTYPE, \
                UPPER(ETHNICITY) as ETHNICITY,\
                UPPER(GENDER) as GENDER,\
                UPPER(LOCATION) as LOCATION,\
                SAMPLEID \
            FROM samples_metadata"

META_df = pd.read_sql(META_sql, con=engine, columns=[META_COLS])

META_WFREQ = pd.read_sql(
    "SELECT WFREQ, SAMPLEID FROM samples_metadata",
    con=engine, columns=[META_COLS])

sample_names = SAMPLES_df.columns
sample_list_names = []
for col in sample_names:
    sample_list_names.append(col)

otu_desc = []
for item in OTU_df["lowest_taxonomic_unit_found"]:
    otu_desc.append(item)

meta_ = META_df
meta_["index"] = "BB_"+meta_["SAMPLEID"].astype(str)
wfreq_ = META_WFREQ
wfreq_["index"] = "BB_"+wfreq_["SAMPLEID"].astype(str)
wfreq_.drop(["SAMPLEID"], axis=1, inplace=True)
wfreq_.set_index("index", inplace=True)

otu_id_sort = OTU_df.sort_index(ascending=False)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/names")
def names():
    names = sample_list_names[0:]
    return jsonify(names)


@app.route("/otu")
def otu():
    otu = otu_desc
    return jsonify(otu)


@app.route("/metadata/<sample>")
def sample_metadata(sample):
    metadata = meta_.to_dict("index")
    return jsonify(metadata)
