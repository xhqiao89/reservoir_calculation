/**
 * Created by sherry on 12/29/17.
 */
var map, pour_point_layer, boundary_layer, reservoir_layer;
var water_level;
var polygon_draw, point_draw, polygon_source, point_source;
var displayStatus = $('#display-status');

$(document).ready(function () {

    map = new ol.Map({
	layers: [ ],
	controls: ol.control.defaults(),
	target: 'map',
	view: new ol.View({
		zoom: 8,
        projection: "EPSG:3857"
	})
    });

    bing_layer = new ol.layer.Tile({
		source: new ol.source.BingMaps({
			imagerySet: 'AerialWithLabels',
			key: 'SFpNe1Al6IDxInoiI7Ta~LX-BVFN0fbUpmO4hIUm3ZA~AsJ3XqhA_0XVG1SUun4_ibqrBVYJ1XaYJdYUuHGqVCPOM71cx-3FS2FzCJCa2vIh'
		})
	});

    point_source = new ol.source.Vector({projection:"EPSG:3857"});
    pour_point_layer = new ol.layer.Vector({
      source: point_source,
      style: new ol.style.Style({
        fill: new ol.style.Fill({
          color: 'rgba(255, 255, 255, 0.2)'
        }),
        stroke: new ol.style.Stroke({
          color: '#ffcc33',
          width: 2
        }),
        image: new ol.style.Circle({
          radius: 7,
          fill: new ol.style.Fill({
            color: '#ffcc33'
          })
        })
      })
    });

    polygon_source = new ol.source.Vector({projection:"EPSG:3857"});
    boundary_layer = new ol.layer.Vector({
    source: polygon_source,
    style: new ol.style.Style({
        stroke: new ol.style.Stroke({
        color: 'blue',
        lineDash: [4],
        width: 3
        }),
        fill: new ol.style.Fill({
        color: 'rgba(0, 0, 255, 0.1)'
        })
    })
    });


    reservoir_layer= new ol.layer.Vector({
    source: new ol.source.Vector({
        features: new ol.format.GeoJSON()
    }),
    style: new ol.style.Style({
        stroke: new ol.style.Stroke({
        color: 'green',
        lineDash: [4],
        width: 3
        }),
        fill: new ol.style.Fill({
        color: 'rgba(0, 255, 0, 0.1)'
        })
    })
    });

    map.addLayer(bing_layer);
    map.addLayer(pour_point_layer);
    map.addLayer(boundary_layer);
    map.addLayer(reservoir_layer);

    var ylat = 40.1;
    var xlon = -111.55;
    CenterMap(xlon,ylat);
    map.getView().setZoom(12);

});

function CenterMap(xlon,ylat){
    var dbPoint = {
        "type": "Point",
        "coordinates": [xlon, ylat]
    };
    var coords = ol.proj.transform(dbPoint.coordinates, 'EPSG:4326','EPSG:3857');
    map.getView().setCenter(coords);
}

function addClickPoint(){
    map.removeInteraction(polygon_draw);
    map.removeInteraction(point_draw);
    pour_point_layer.getSource().clear();
    reservoir_layer.getSource().clear();

    point_draw = new ol.interaction.Draw({
        source: point_source,
        type: 'Point'
      });
    map.addInteraction(point_draw);
}

function draw_polygon(value){
    map.removeInteraction(polygon_draw);
    map.removeInteraction(point_draw);

    boundary_layer.getSource().clear();
    reservoir_layer.getSource().clear();

    if (value !== 'None') {
      polygon_draw = new ol.interaction.Draw({
        source: polygon_source,
        type: 'Polygon'
      });
      map.addInteraction(polygon_draw);
    }
  }

function geojson2feature(myGeoJSON) {
    //Convert GeoJSON object into an OpenLayers 3 feature.
    var geojsonformatter = new ol.format.GeoJSON();
    var myFeature = geojsonformatter.readFeatures(myGeoJSON);
    //var myFeature = new ol.Feature(myGeometry);
    return myFeature;

}

function feature2geojson(myFeature) {
    //Convert an OpenLayers 3 feature to GeoJSON object
    var geojsonformatter = new ol.format.GeoJSON();
    var myGeojson = geojsonformatter.writeFeature(myFeature,{featureProjection:'EPSG:3857', dataProjection:'EPSG:3857'});
    //var myFeature = new ol.Feature(myGeometry);
    return myGeojson;

}

function run_rc() {

    map.removeInteraction(polygon_draw);
    map.removeInteraction(point_draw);

    water_level=document.getElementById("waterLevel").value;

    if (pour_point_layer.getSource().getFeatures().length ==0 || boundary_layer.getSource().getFeatures().length==0){
        displayStatus.addClass('error');
        displayStatus.html('<em>Error. Please select pour point AND draw polygon first. </em>');
        return

    } else {
        var point_geojson = feature2geojson(pour_point_layer.getSource().getFeatures()[0])
        alert(point_geojson);
        var boundary_geojson = feature2geojson(boundary_layer.getSource().getFeatures()[0])
        alert(boundary_geojson);

        displayStatus.removeClass('success');
        displayStatus.removeClass('error');
        displayStatus.addClass('calculating');
        displayStatus.html('<em>Calculating...</em>');

        $.ajax({
        type: 'GET',
        url: 'run',
        dataType:'json',
        data: {
                'boundary_geojson': boundary_geojson,
                'point_geojson': point_geojson,
                'water_level':water_level,
                'prj' : "native"
        },
        success: function (data) {

            reservoir_layer.getSource().addFeatures(geojson2feature(data.lake_data));
            displayStatus.removeClass('calculating');
            displayStatus.addClass('success');
            displayStatus.html('<em>Success! The reservoir volume is </em>'+ data.lake_volume + 'cubic meters.');

        },
        error: function (jqXHR, textStatus, errorThrown) {
            alert("Error");
            displayStatus.removeClass('calculating');
            displayStatus.addClass('error');
            displayStatus.html('<em>' + errorThrown + '</em>');
        }
    });






    }




//
//     basin_layer.getSource().clear();
//     snap_point_layer.getSource().clear();
//
//     displayStatus.removeClass('error');
//     displayStatus.addClass('calculating');
//     displayStatus.html('<em>Calculating...</em>');
//

}
