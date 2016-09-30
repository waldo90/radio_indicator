# sudo apt-get install python-appindicator
import gtk
import pygtk
import requests
pygtk.require('2.0')


have_appindicator = True
try:
    import appindicator
except:
    have_appindicator = False


class RadioStation(object):

    def __init__(self, station_name, poll_interval=20000):
        self.poll_interval_ms = poll_interval
        self.station_name = station_name
        self.song = ''
        self.artist = ''
        self.start_time = ''
        self.reading = False

    def read(self):
        if self.reading:
            return
        self.reading = True
        self.query_station()
        self.reading = False
        return True

    def query_station(self):
        try:
            response = requests.get(self.info_url, timeout=5)
        except requests.exceptions.Timeout:
            return None
        except:
            return None
        if response.status_code == requests.codes.ok:
            return response
        return None


class KEXP(RadioStation):
    info_url = "http://kexp.org/s/s.aspx/?x=3"  # Param x=3 requests json

    def __init__(self):
        super(KEXP, self).__init__('KEXP')

    def query_station(self):
        response = super(KEXP, self).query_station()
        if response is None:
            return True
        try:
            data = response.json()
        except:
            return True
        if data.get('AirBreak') is True:
            self.artist = 'Show'
            self.song = "Airbreak"
            return True
        self.album = data.get('Album')
        self.artist = data.get('Artist')
        self.song = data.get('SongTitle')
        self.art_url = data.get('AlbumArt')
        self.start_time = data.get('TimePlayer')
        return True


class FIP(RadioStation):
    info_url = "http://www.fipradio.fr/sites/default/files/import_si/si_titre_antenne/FIP_player_current.json"

    def __init__(self):
        super(FIP, self).__init__('FIP')

    def query_station(self):
        response = super(FIP, self).query_station()
        if response is None:
            return True
        try:
            player = response.json()
        except:
            return True
        current = player.get('current')
        if current is None:
            return True
        song = current.get('song')
        if song is None:
            return True

        artist = song.get('interpreteMorceau')
        track = song.get('titre')

        if None in (artist, track):
            return True
        self.artist = artist.title()
        self.song = track.title()
        self.start_time = song.get('startTime')
        return True


class RadioIndicator(object):

    isAboutOpen = False

    def __init__(self, station=None):
        self.station = station
        if have_appindicator:
            self.ind = appindicator.Indicator("example-simple-client",
                                              "indicator-messages",
                                              appindicator.CATEGORY_APPLICATION_STATUS)
            self.ind.set_status(appindicator.STATUS_ACTIVE)
            self.ind.set_attention_icon("new-messages-red")
            self.ind.set_icon("rhythmbox-panel")
            self.update_stream_info()
            gtk.timeout_add(self.station.poll_interval_ms, self.update_stream_info)

        else:
            self.ind = gtk.status_icon_new_from_stock(gtk.STOCK_HOME)

        # Create menu object
        self.menu = gtk.Menu()
        # About
        menuItemAbout = gtk.MenuItem('About')
        menuItemAbout.connect("activate", self.about_response, "About")
        self.menu.append(menuItemAbout)
        # Stations
        menuItemStations = gtk.MenuItem('Stations')
        stationmenu = gtk.Menu()
        kexpItem = gtk.MenuItem('KEXP')
        fipItem = gtk.MenuItem('FIP')
        kexpItem.connect("activate", self.change_station, "kexp")
        fipItem.connect("activate", self.change_station, "fip")
        stationmenu.append(kexpItem)
        stationmenu.append(fipItem)
        menuItemStations.set_submenu(stationmenu)
        self.menu.append(menuItemStations)
        # Track logging
        mi_log = gtk.MenuItem('Log Track')
        mi_log.connect("activate", self.log_track, "Log Track")
        self.menu.append(mi_log)
        # Quit
        menuItemQuit = gtk.MenuItem('Quit')
        menuItemQuit.connect('activate', self.quit)
        self.menu.append(menuItemQuit)

        self.menu.show_all()
        self.ind.set_menu(self.menu)

    def quit(self, widget, data=None):
        gtk.main_quit()

    def about_response(self, w, param):
        if self.isAboutOpen is False:
            self.isAboutOpen = True
            # Show about window
            # actually show a constructed window
            # MAKE CERTAIN that the isAboutOpen property is set to False when the window
            # is destroyed!
            self.window_about = gtk.Window(gtk.WINDOW_TOPLEVEL)
            self.window_about.connect('destroy', self.about_destroy)
            self.window_about.show()

    def about_destroy(self, widget, data=None):
        self.isAboutOpen = False

    def change_station(self, w, param):
        if param == 'kexp':
            self.station = KEXP()
        if param == 'fip':
            self.station = FIP()
        self.update_stream_info()

    def log_track(self, w, param):
        with open("/home/pat/Desktop/radio_log.txt", 'a') as log_file:
            log_file.write(self.ind.get_label() + '\n')

    def update_stream_info(self):
        if not hasattr(self, 'station'):
            return True
        self.station.read()
        self.ind.set_label("|{}| {} : {}  ".format(self.station.station_name,
                                                   self.station.artist,
                                                   self.station.song))
        return True


def main():
    gtk.main()
    return 0

if __name__ == "__main__":
    indicator = RadioIndicator(FIP())
    main()
