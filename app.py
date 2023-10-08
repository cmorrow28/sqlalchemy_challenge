#################################################
# Dependencies
#################################################

import numpy as np
import datetime as dt

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
station = Base.classes.station
measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
# Define a session factory function
def create_session():
    return Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def homepage():
    # List all available api routes
    return (
        f"Hawaii Weather API:<br/><br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
        f"NOTICE:<br/>"
        f"Query date is in ISO date format(YYYY-MM-DD),<br/>"
        f"Data dates start at 2010-01-01 and end at 2017-08-23."
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create a session using the create_session() function
    session = create_session()
    
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query the precipitation data for the last year
    results = session.query(measurement.date, measurement.prcp).filter(measurement.date >= one_year_ago).all()

    # Convert the query results to a dictionary
    precipitation_data = {}
    for date, prcp in results:
        precipitation_data[date] = prcp

    # Close the session to release resources
    session.close()

    return jsonify(precipitation_data)

# Create the /api/v1.0/stations route
@app.route("/api/v1.0/stations")
def stations():
    # Create a session using the create_session() function
    session = create_session()
    
    # Query the list of stations
    results = session.query(station.station).all()

    # Convert the query results to a list
    stations_list = [station[0] for station in results]

    return jsonify(stations_list)

# Create the /api/v1.0/tobs route
@app.route("/api/v1.0/tobs")
def tobs():
    # Create a session using the create_session() function
    session = create_session()
    
    # Calculate the date one year ago from the last date in the database
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()
    last_date = dt.datetime.strptime(last_date[0], "%Y-%m-%d")
    one_year_ago = last_date - dt.timedelta(days=365)

    # Query the temperature observations for the most active station for the last year
    most_active_station = session.query(measurement.station).\
        group_by(measurement.station).\
        order_by(func.count().desc()).first()[0]
    
    results = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_station).\
        filter(measurement.date >= one_year_ago).all()

    # Convert the query results to a list of dictionaries
    tobs_data = []
    for date, tobs in results:
        tobs_data.append({"date": date, "temperature": tobs})

    return jsonify(tobs_data)

# Create the /api/v1.0/<start> route
@app.route("/api/v1.0/<start>")
def temp_start(start):
    # Create a session using the create_session() function
    session = create_session()
    
    # Convert the start date string to a datetime object
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")

    # Calculate the temperature statistics for the specified start date and all subsequent dates
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).all()

    # Create a dictionary with the temperature statistics
    temp_dict = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_dict)

# Create the /api/v1.0/<start>/<end> route
@app.route("/api/v1.0/<start>/<end>")
def temp_range(start, end):
    # Create a session using the create_session() function
    session = create_session()
    
    # Convert the start and end date strings to datetime objects
    start_date = dt.datetime.strptime(start, "%Y-%m-%d")
    end_date = dt.datetime.strptime(end, "%Y-%m-%d")

    # Calculate the temperature statistics for the specified date range
    results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).\
        filter(measurement.date <= end_date).all()

    # Create a dictionary with the temperature statistics
    temp_dict = {
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_dict)

if __name__ == '__main__':
    app.run(debug=True)