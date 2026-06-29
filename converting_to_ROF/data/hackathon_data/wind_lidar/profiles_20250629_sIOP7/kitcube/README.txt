(base) stefano@stefano-XPS-13-9340:~$ for i in *0630*nc; do echo $i; ncdump -h $i |grep station_name; done
HYB_20250630_600s_100m_wind_profile.nc
		:station_name = "Kollmann" ;
WLS200s_115_20250630_600s_100m_wind_profile.nc
		:station_name = "Sarnthein" ;
WLS200s_124_20250630_600s_100m_wind_profile.nc
		:station_name = "St. Martin" ;
WLS200s_125_20250630_600s_100m_wind_profile.nc
		:station_name = "Naturns" ;
WLS200s_159_20250630_600s_100m_wind_profile.nc
		:station_name = "Gargazon" ;
WLS200s_172_20250630_600s_100m_wind_profile.nc
		:station_name = "Mittewald" ;
WTX_20250630_600s_100m_wind_profile.nc
		:station_name = "Bozen" ;

(base) stefano@stefano-XPS-13-9340:~$ for i in *0630*nc; do echo $i; ncdump -h $i |grep "latitude = "; done
HYB_20250630_600s_100m_wind_profile.nc
		:latitude = 46.595116 ;
WLS200s_115_20250630_600s_100m_wind_profile.nc
		:latitude = 46.634911 ;
WLS200s_124_20250630_600s_100m_wind_profile.nc
		:latitude = 46.784444 ;
WLS200s_125_20250630_600s_100m_wind_profile.nc
		:latitude = 46.647873 ;
WLS200s_159_20250630_600s_100m_wind_profile.nc
		:latitude = 46.576216 ;
WLS200s_172_20250630_600s_100m_wind_profile.nc
		:latitude = 46.806893 ;
WTX_20250630_600s_100m_wind_profile.nc
		:latitude = 46.45523 ;

(base) stefano@stefano-XPS-13-9340:~$ for i in *0630*nc; do echo $i; ncdump -h $i |grep "longitude = "; done
HYB_20250630_600s_100m_wind_profile.nc
		:longitude = 11.529069 ;
WLS200s_115_20250630_600s_100m_wind_profile.nc
		:longitude = 11.359278 ;
WLS200s_124_20250630_600s_100m_wind_profile.nc
		:longitude = 11.231075 ;
WLS200s_125_20250630_600s_100m_wind_profile.nc
		:longitude = 10.991185 ;
WLS200s_159_20250630_600s_100m_wind_profile.nc
		:longitude = 11.200041 ;
WLS200s_172_20250630_600s_100m_wind_profile.nc
		:longitude = 11.57206 ;
WTX_20250630_600s_100m_wind_profile.nc
		:longitude = 11.32158 ;

(base) stefano@stefano-XPS-13-9340:~$ for i in *0630*nc; do echo $i; ncdump -h $i |grep "altitude = "; done
HYB_20250630_600s_100m_wind_profile.nc
		:altitude = 466. ;
WLS200s_115_20250630_600s_100m_wind_profile.nc
		:altitude = 986. ;
WLS200s_124_20250630_600s_100m_wind_profile.nc
		:altitude = 594. ;
WLS200s_125_20250630_600s_100m_wind_profile.nc
		:altitude = 541. ;
WLS200s_159_20250630_600s_100m_wind_profile.nc
		:altitude = 254. ;
WLS200s_172_20250630_600s_100m_wind_profile.nc
		:altitude = 802. ;
WTX_20250630_600s_100m_wind_profile.nc
		:altitude = 235. ;

