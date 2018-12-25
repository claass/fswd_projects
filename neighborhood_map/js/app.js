
function go(){

  /***************
  Model
  ***************/

  var locations = [
    {title: 'Tartine Bakery', location: {lat: 37.7629671,lng: -122.427464}, foursq: '42814b00f964a52002221fe3'},
    {title: "Devil's Teeth Baking Company", location: {lat: 37.7529148,lng: -122.5056914}, foursq: '4db0bc8e0437a93f7f7a23e7'},
    {title: "Bob's Donuts", location: {lat: 37.7918869,lng: -122.423315}, foursq: '44cf44a2f964a52020361fe3'},
    {title: 'Dynamo Donuts', location: {lat: 37.7667792,lng: -122.4304372}, foursq: '49ccf971f964a520a6591fe3'},
    {title: 'The Mill', location: {lat: 37.7780098,lng: -122.4308484}, foursq: '4feddd79d86cd6f22dc171a9'},
  ];

  /***************
  ViewModel
  ***************/

  var viewModel = function () {
    //VM of Hood
    var self = this;

    //Setting up attributes
    self.map = {};                                  //Map object
    self.textInput = ko.observable('');             //Search input string
    self.markers = ko.observableArray([]);          //List of markers
    self.filteredMarkers = ko.computed(function(){  //Filterd markers for list
      return ko.utils.arrayFilter( self.markers(), function(marker){
        if (self.textInput().length > 0){
          return marker.title.toLowerCase().indexOf(self.textInput()) !== -1;
        } else {
          return true;
        }
      });
    });                                             //List of visibile markers
    self.infowindow = new google.maps.InfoWindow(); //infowindow object
    self.infotemp = "<div class='infowindow'>"                                                              +
                          "<h5>%title%</h5>"                                                                +
                          "<div>"                                                                           +
                              "<div id='foursq'>"                                                           +
                                  "<p id='rating'>The Foursquare rating for this place is: loading...</p>"  +
                              "</div>"                                                                      +
                          "</div>"                                                                          +
                    "<div>";                      //html template for info window

    /* ----------------- Map and marker setup -----------------*/

    //Initialize map element
    self.initMap = function () {
      self.map = new google.maps.Map(document.getElementById('map'),{
        center: {lat: 37.7779204, lng: -122.4167777},
        zoom: 13
      });

      //To be used in loop: function to add event listener to marker object
      function addListenerToMarker(marker){
        marker.addListener('click', function(){
          self.markerclick(this);
        });
      }

      //Create bounds object
      var bounds = new google.maps.LatLngBounds();

      //make markers during Initialize process
      for (var i=0; i<locations.length; i++) {
        var position = locations[i].location;
        var title = locations[i].title;
        var venueid = locations[i].foursq;
        var marker = new google.maps.Marker({
          map: self.map,
          position: position,
          title: title,
          animation: google.maps.Animation.DROP,
          id: i,
          venueid: venueid,
          rating: '',
        });

        addListenerToMarker(marker);

        //push the marker to the array of markers
        self.markers.push(marker);
        //extend the map bounds by this markers position
        bounds.extend(self.markers()[i].position);
      }
      //fit map within the bounds at setup
      self.map.fitBounds(bounds);

      //add eventLsitener to resizing the window
      google.maps.event.addDomListener(window,'resize',function(){
        self.map.fitBounds(bounds);
      });
    };

    /* --------------- User clicks  -------------------*/

    //populate info window
    self.markerclick = function(marker) {
      //make sure are marker was input
      if (self.infowindow.marker != marker) {
        self.infowindow.marker = marker;

        //Animate marker
        marker.setAnimation(google.maps.Animation.BOUNCE);
        setTimeout(function(){marker.setAnimation(null);}, 3000);

        //Third party AJAX calls
        self.foursquareCall(marker);

        //set window content
        self.infowindow.setContent(
          self.infotemp.replace('%title%', marker.title));

        //open the marker window
        self.infowindow.open(map, marker);

        //add Eventlistener for clicking on close
        self.infowindow.addListener('closeclick', function(){
          self.infowindow.setMarker = null;
        });
      }
    };

    /* ------------- Other API Handlers  --------------*/

    // AJAX request for Foursquare scrore
    self.foursquareCall = function(marker) {
      var url = 'https://api.foursquare.com/v2/venues/%venueid%?v=20131016&client_id=YHTQ5AZUA2XMOWJSEWPX2DS5SZOJ15JQVOCCEWDUZTOL1E1Z&client_secret=P0DTE1R1LHHYXCGSY10Q32H3DQV5MFHNBVM53R512HLXWWPQ';
      url = url.replace('%venueid%', marker.venueid);

      if (marker.rating === '' ) {
        $.ajax({
          url: url,
          success: function(data) {
            self.infowindow.setContent(
              self.infowindow.getContent().replace(
                'loading...', data.response.venue.rating
              )
            );
          },
          error: function(data) {
            self.infowindow.setContent(
              self.infowindow.getContent().replace(
                'loading...', 'Something did not work out. Sorry :'
              )
            );
          },
        });
      }
    };

    /* --------------- Filter Handler  ----------------*/

    self.filterLocations = function(){
      //Clear filteredMarkers List
      // self.filteredMarkers() =
      //Iterate through markers and check if textInput is within title
      for (var i=0; i<self.markers().length; i++){
        if (self.markers()[i].title.toLowerCase().indexOf(self.textInput()) !== -1) {
          self.markers()[i].setMap(self.map);
        } else {
          self.markers()[i].setMap(null);
        }
      }
    };
    //Kick off the map creation process
    this.initMap();
    };
  //TODO add error and success handling
  ko.applyBindings(new viewModel());
}

/***************
Error Handling for GoogleMaps (defined outside of go())
***************/
function googleError () {
  alert("Google API responded with an error :(");
}
