import os
import binascii
import json
import geojson

from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from tethys_sdk.gizmos import Button,TextInput
from tethys_apps.tethysapp.reservoir_calculation.grassfunctions import RC

@login_required()
def home(request):
    """
    Controller for the app home page.
    """
    btnCalc = Button(display_text="Calculate Storage Capacity",
                      name="btnCalc",
                      attributes="onclick=run_rc()",
                      submit=False)

    btnDrawPolygon = Button(display_text="Draw Reservoir Maximum Boundary",
                      name="btnDraw",
                      attributes="onclick=draw_polygon()",
                      submit=False)
    btnClickPoint = Button(display_text="Select pour point",
                     name="btnClickPoint",
                     attributes="onclick=addClickPoint()",
                     submit=False)
    waterLevel = TextInput(display_text='Water Level (m):',
                          name="waterLevel",
                          initial="50",
                          disabled=False,
                          attributes="")

    context = {
        'btnCalc': btnCalc,
        'btnDrawPolygon': btnDrawPolygon,
        'btnClickPoint':btnClickPoint,
        'waterLevel':waterLevel
    }

    return render(request, 'reservoir_calculation/home.html', context)


@login_required()
def run_rc(request):

    string_length = 4
    jobid = binascii.hexlify(os.urandom(string_length))
    message = ""

    try:
        if request.GET:
            boundary_geojson = request.GET.get("boundary_geojson", None)
            point_geojson = request.GET.get("point_geojson", None)

            # extract xy from point_geojson content
            point_geojson_obj = geojson.loads(point_geojson)
            xlon = point_geojson_obj.geometry.coordinates[0]
            ylat = point_geojson_obj.geometry.coordinates[1]

            water_level = request.GET.get("water_level", None)
            prj = request.GET.get("prj", None)


            # Run RC()
            RC_dict= RC(jobid, boundary_geojson, xlon, ylat, water_level, prj)


            lake_GEOJSON = RC_dict["lake_GEOJSON"]
            lake_volume = RC_dict["lake_volume"]
            msg=RC_dict["msg"]
            status=RC_dict["status"]

            # Check results
            if lake_GEOJSON is not None:
                message += msg
            else:
                message += msg
        else:
            raise Exception("Please call this service in a GET request.")

    except Exception as ex:
        message = ex.message
        print ex
        print ex.message

    # Return inputs and results
    finally:

        with open(lake_GEOJSON) as f:
            lake_data = json.load(f)

        return JsonResponse({"lake_data":lake_data,
                             "lake_volume":lake_volume
                        })
