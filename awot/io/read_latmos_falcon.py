"""
awot.io.read_latmos_falcon
=========================

This is a grouping of scripts designed to process (French) 
 Falcon distributed by LATMOS.
 
The data are in NetCDF format.

Author: Nick Guy, 19 Nov 2014.

"""
# NOTES:: This has only been tested with DYNAMO data files, versions
#         may change and another function may be needed.
#-------------------------------------------------------------------
# Load the needed packages
from netCDF4 import Dataset, num2date, date2num
import datetime
import numpy as np
import pytz
#-------------------------------------------------------------------
#===============================================================
# BEGIN FUNCTIONS
#===============================================================
def flight_data(fname):
    '''A wrapper to call the rasta_dynamic'''
    data = rasta_dynamic(fname)
    
    return data

def rasta_wind(fname):
    '''A wrapper to call the rasta_dynamic module'''
    data = rasta_dynamic(fname)
    
    return data
    
def rasta_radar(fname):
    '''A wrapper to call the rasta_dynamic module'''
    data = rasta_dynamic(fname)
    
    return data
    
def rasta_radonvar(fname):
    '''A wrapper to call the rasta_microphysics module'''
    data = rasta_microphysics(fname)
    
    return data
    
def rasta_dynamic(fname):
    '''
    Read in NetCDF data file containing Falcon dynamic properties 
    retrieved from radar measurements.
    
    PARAMETERS::
    ----------
    fname : string
        Filename [string]
    
    OUTPUT::
    ------
    data : Dictionary of the following values
    
    Lat : float
        Aircraft latitude [decimal degrees]
    Lon : float
        Aircraft longitude [decimal degrees]
    Alt : float
        Aircraft altitude via GPS [km]
    Ht : float
        Height [km]
    temp : float
        Temperature at aircraft altitude [degrees C]
    pressure: float
        Pressure at aircraft altitude [hPa]
    Vx_flight_level : float
        Vx at flight level from in situ measurements [m/s]
    Vy_flight_level : float
        Vy at flight level from in situ measurements [m/s]
    Vz_flight_level : float
        Vz at flight level from in situ measurements [m/s]
    zonal_wind : float
        Zonal wind component [m/s]
    meridional_wind : float
        Meriodional wind component [m/s]
    fields : Dictionary of variables in file
        reflectivity : float
            Radar Reflectivity [dBZ]
        Uwind : float
            Wind along aircraft longitudinal axis wind [m/s]
        Vwind : float
            Wind perpendicular to aircraft longitudinal axis wind [m/s]
        Wwind : float
            Vertical wind component [m/s]
        term_fall_speed : float
            Terminal fall speed [m/s]
        term_fall_speed_weighted : float
            Terminal fall speed weighted by Vt-Z [m/s]
        metadata : Dictionary of global attributes in file
    '''
    
    # Read the NetCDF
    ncFile = Dataset(fname,'r')
    ncvars = ncFile.variables
    
    # Grab the metadata stored in global attributes as a dictionary
    metadata = ncFile.__dict__

    # Pull out the date, convert the date to a datetime friendly string
    # Adds dashes between year, month, and day
    # This assumes that the date is the 2nd instance in the filename!!
    yyyymmdd = fname.split("_")[1]
    StartDate = yyyymmdd[0:4] + '-' + yyyymmdd[4:6] + '-' + yyyymmdd[6:8]
    
    # Create the time array
    # First find the good indices, there can be missing values 
    # in Falcon Data (seriously come on!)
    # So we have remove these indices from all fields in the future

    # Find the indices of not missing points
    Good = np.where(~np.isnan(ncFile.variables['time'][:]))

    # Now convert the time array into a datetime instance
    dtHrs = num2date(ncFile.variables['time'][Good], 'hours since ' + StartDate +  '00:00:00+0:00')
    # Now convert this datetime instance into a number of seconds since Epoch
    TimeSec = date2num(dtHrs, 'seconds since 1970-01-01 00:00:00+0:00')
    # Now once again convert this data into a datetime instance
    Time_unaware = num2date(TimeSec, 'seconds since 1970-01-01 00:00:00+0:00')
    Time = Time_unaware#.replace(tzinfo=pytz.UTC)
    
    # Pull out each variable
    try:
        Lat = ncFile.variables['latitude'][Good]
    except:
        Lat = None
    try:
        Lon = ncFile.variables['longitude'][Good]
    except:
        Lon = None
    try:
        Ht = _nc_height_var_to_dict(ncvars['height'])
        Ht['data'][:] = Ht['data'][:] * 1000.
        Ht['units'] = 'meters'
    except:
        Ht = None
    try:
        Alt = ncFile.variables['altitude'][Good] * 1000.
    except:
        Alt = None
    try:
        temp = ncFile.variables['temperature'][Good]
    except:
        temp = None
    try:
        pressure = ncFile.variables['pressure'][Good]
    except:
        pressure = None
    try:
        Vx_flight_level = ncFile.variables['Vx_insitu'][Good]
    except:
        Vx_flight_level = None
    try:
        Vy_flight_level = ncFile.variables['Vy_insitu'][Good]
    except:
        Vy_flight_level = None
    try:
        Vz_flight_level = ncFile.variables['Vz_insitu'][Good]
    except:
        Vz_flight_level = None
    try:
        zonal_wind = ncFile.variables['VE'][Good, :]
    except:
        zonal_wind = None
    try:
        meridional_wind = ncFile.variables['VN'][Good, :]
    except:
        meridional_wind = None
    try:
        mask_hydro = _nc_radar_var_to_dict(ncvars['Mask'], Good)
    except:
        mask_hydro = None

    # Add fields to their own dictionary
    fields = {}
    # Read the Reflectivity
    fields['dBZ'] = _nc_radar_var_to_dict(ncvars['Z'], Good)
    
    # Read the U wind (Along aircraft longitudinal axis)
    fields['Uwind'] = _nc_radar_var_to_dict(ncvars['Vx'], Good)
    
    # Read the V wind (Perpendicular to aircraft longitudinal axis)
    fields['Vwind'] = _nc_radar_var_to_dict(ncvars['Vy'], Good)
    
    # Read the vertical wind
    fields['Wwind'] = _nc_radar_var_to_dict(ncvars['Vz'], Good)
    
    # Read the terminal velocity
    fields['term_fall_speed'] = _nc_radar_var_to_dict(ncvars['Vt'], Good)
    fields['term_fall_speed_weighted'] = _nc_radar_var_to_dict(ncvars['Vt_weighted'], Good)
    
    # Pull out global attributes
    try:
        ncFile.ProjectName
        project = ncFile.ProjectName
    except:
        project = fname.split("_")[0]
    try:
        ncFile.FlightNumber
        flightnum = ncFile.FlightNumber
    except:
        flightnum = fname.split("_")[2]
    
    # Set the platform
    platform = 'falcon'
    
    # Now mask missing values
    if Lat is not None:
        np.ma.masked_invalid(Lat)
    if Lon is not None:
        np.ma.masked_invalid(Lon)
    if Alt is not None:
        np.ma.masked_invalid(Alt)
    if temp is not None:
        np.ma.masked_invalid(temp)
    if pressure is not None:
        np.ma.masked_invalid(pressure)
    if Vx_flight_level is not None:
        np.ma.masked_invalid(Vx_flight_level)
    if Vy_flight_level is not None:
        np.ma.masked_invalid(Vy_flight_level)
    if Vz_flight_level is not None:
        np.ma.masked_invalid(Vz_flight_level)

    # Create a dictionary to transfer the data
    data = {'time': Time,
            'latitude': Lat,
            'longitude': Lon,
            'height': Ht,
            'altitude': Alt,
            'temperature': temp,
            'pressure': pressure,
            'Vx_flight_level': Vx_flight_level,
            'Vy_flight_level': Vy_flight_level,
            'Vz_flight_level': Vz_flight_level,
            'zonal_wind': zonal_wind,
            'meridional_wind': meridional_wind,
            'fields': fields,
            'metadata': metadata,
            'project' : project,
            'platform': platform,
            'flight_number': flightnum,
            }
    
    ncFile.close()
    
    return data
    
###############

def rasta_microphysics(fname):
    '''
    Read in NetCDF data file containing Falcon microphysical properties.
    
    PARAMETERS::
    ----------
        fname : string
            Filename [string]
    
    OUTPUT::
    ------
        data : Dictionary of the following values
            Lat : float
                Aircraft latitude [decimal degrees]
            Lon : float
                Aircraft longitude [decimal degrees]
            Ht : float
                Height [km]
            extinction : float
                Visible extinction [1/m]
            Time : float
                Aircraft time array
            n0start : float
                Normalized concentration parameter [m^-4]
            iwc : float
                Ice water content [kg m^-3]
            effective_radius : float
                Effective radius [micron]
            Dm : float
                Equivalen volume weighted diameter [micron]
            Nt : float
                Number_concentration [m^-3]
            dBZ : float
                Radar reflectivity [dBZ]
            Z_fwd : float
                Forward-modelled radar reflectivity [dBZ]
            Vt : float
                Terminal fall velocity [m s^-1]
            Vt_fwd : float
                Forward-modelled terminal fall velocity [m s^-1]
            temp : float
                Temperature [degrees C]
            aM : float
                Retrieved aM (M (D)=aD^b) [unitless]
       
    USAGE::
    -----
     data = flight_track(fname)
    '''
    
    # Read the NetCDF
    ncFile = Dataset(fname,'r')
    
    # Grab the metadata stored in global attributes as a dictionary
    metadata = ncFile.__dict__

    # Pull out the date, convert the date to a datetime friendly string
    # Adds dashes between year, month, and day
    # This assumes that the date is the 2nd instance in the filename!!
    yyyymmdd = fname.split("_")[1]
    StartDate = yyyymmdd[0:4] + '-' + yyyymmdd[4:6] + '-' + yyyymmdd[6:8]
    
    # Grab the time array
    # There can be missing values in Falcon Data (seriously come on!)
    # So we have remove these indices from all fields in the future
    TimeHrs = np.ma.masked_invalid(ncFile.variables['time'][:])
    # Find the indices of not missing points
    Good = np.where(~np.isnan(TimeHrs))
    
    Time_unaware = num2date(TimeHrs[Good]*3600.,'seconds since 1970-01-01 00:00:00+0:00')
    Time = Time_unaware#.replace(tzinfo=pytz.UTC)
    
    # Pull out each variable
    try:
        Lat = ncFile.variables['latitude'][Good]
    except:
        Lat = None
    try:
        Lon = ncFile.variables['longitude'][Good]
    except:
        Lon = None
    try:
        Ht = ncFile.variables['height'][:] * 1000.
    except:
        Ht = None
    try:
        extinction = ncFile.variables['extinction'][:, Good]
    except:
        extinction = None
    try:
        n0start = ncFile.variables['n0star'][:, Good]
    except:
        n0start = None
    try:
        iwc = ncFile.variables['iwc'][:, Good]
    except:
        iwc = None
    try:
        effective_radius = ncFile.variables['effective_radius'][:, Good]
    except:
        effective_radius = None
    try:
        Dm = ncFile.variables['Dm'][:, Good]
    except:
        Dm = None
    try:
        Nt = ncFile.variables['Nt'][:, Good]
    except:
        Nt = None
    try:
        dBZ = ncFile.variables['Z'][:, Good]
    except:
        dBZ = None
    try:
        Z_fwd = ncFile.variables['Z_fwd'][:, Good]
    except:
        Z_fwd = None
    try:
        Vt = ncFile.variables['vt'][:, Good]
    except:
        Vt = None
    try:
        Vt_fwd = ncFile.variables['vt_fwd'][:, Good]
    except:
        Vt_fwd = None
    try:
        temp = ncFile.variables['T'][:, Good]
    except:
        temp = None
    try:
        aM = ncFile.variables['aM'][:, Good]
    except:
        aM = None
    
    # Pull out global attributes
    try:
        ncFile.ProjectName
        project = ncFile.ProjectName
    except:
        project = fname.split("_")[0]
    try:
        ncFile.FlightNumber
        flightnum = ncFile.FlightNumber
    except:
        flightnum = fname.split("_")[2]
    
    # Set the platform
    platform = 'falcon'
    
    # Now mask missing values
    if Lat is not None:
        np.ma.masked_invalid(Lat)
    if Lon is not None:
        np.ma.masked_invalid(Lon)
    if Ht is not None:
        np.ma.masked_invalid(Ht)
    if extinction is not None:
        np.ma.masked_invalid(extinction)
    if n0start is not None:
        np.ma.masked_invalid(n0start)
    if iwc is not None:
        np.ma.masked_invalid(iwc)
    if effective_radius is not None:
        np.ma.masked_invalid(effective_radius)
    if Dm is not None:
        np.ma.masked_invalid(Dm)
    if Nt is not None:
        np.ma.masked_invalid(Nt)
    if dBZ is not None:
        np.ma.masked_invalid(dBZ)
    if Z_fwd is not None:
        np.ma.masked_invalid(Z_fwd)
    if Vt is not None:
        np.ma.masked_invalid(Vt)
    if Vt_fwd is not None:
        np.ma.masked_invalid(Vt_fwd)
    if temp is not None:
        np.ma.masked_invalid(temp)
    if aM is not None:
        np.ma.masked_invalid(aM)

    # Create a dictionary to transfer the data
    data = {'time': Time,
            'latitude': Lat,
            'longitude': Lon,
            'height': Ht,
            'extinction': extinction,
            'n0start': n0start,
            'iwc': iwc,
            'effective_radius': effective_radius,
            'Dm': Dm,
            'Nt': Nt,
            'dBZ': dBZ,
            'Z_fwd': Z_fwd,
            'term_velocity': Vt,
            'term_velocity_fwd': Vt_fwd,
            'temperature': temp,
            'aM': aM,
            'metadata': metadata,
            'project' : project,
            'platform': platform,
            'flight_number': flightnum,
            }
    
    ncFile.close()
    
    return data

    
###########################
# Create Variable methods #
###########################

def _nc_radar_var_to_dict(ncvar, Good_Indices):
    """ Convert a NetCDF Dataset variable to a dictionary. 
    Appropriated from PyArt package
    """
    d = dict((k, getattr(ncvar, k)) for k in ncvar.ncattrs())
    d['data'] = ncvar[:]
    if np.isscalar(d['data']):
        # netCDF4 1.1.0+ returns a scalar for 0-dim array, we always want
        # 1-dim+ arrays with a valid shape.
        d['data'] = np.array(d['data'][Good_Indices, :])
        d['data'].shape = (1, )
    return d

def _nc_height_var_to_dict(ncvar):
    """ Convert a NetCDF Dataset variable to a dictionary. 
    Appropriated from PyArt package
    """
    d = dict((k, getattr(ncvar, k)) for k in ncvar.ncattrs())
    d['data'] = ncvar[:]
    if np.isscalar(d['data']):
        # netCDF4 1.1.0+ returns a scalar for 0-dim array, we always want
        # 1-dim+ arrays with a valid shape.
        d['data'] = np.array(d['data'][:])
        d['data'].shape = (1, )
    return d