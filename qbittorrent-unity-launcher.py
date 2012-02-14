#!/usr/bin/python

# -*- coding: utf-8 -*-
# Licensed under the MIT license.

import sys
import logging
import argparse

import qbittorrentrpc

from gi.repository import Unity, GLib, GObject, Dbusmenu

# Dirty hack.
# GLib functions `spawn_async` and `child_watch_add` in `python-gobject` package
# from Ubuntu 11.04 and 11.10 are completely different: they require arguments
# in different order and returns different results.
# Use adapter functions to work around.
if (GLib.MAJOR_VERSION, GLib.MINOR_VERSION) < (2, 30):
    def spawn_async(argv, flags):
        _, pid = GLib.spawn_async(
            None, # Inherit current directory,
            argv, # Command with arguments.
            None, # Inherit environment.
            flags,
            None, # Child setup callback.
            None # User data.
        )
        return pid

    def child_watch_add(priority, pid, on_closed, data):
        return GLib.child_watch_add(priority, pid, on_closed, data)

else:
    def spawn_async(argv, flags):
        pid, _, _, _ = GLib.spawn_async(argv=argv, flags=flags)
        return pid

    def child_watch_add(priority, pid, on_closed, data):
        return GLib.child_watch_add(priority=priority, pid=pid, function=on_closed, data=data)

class UnityLauncherEntry:
	def __init__(self, name):
		self.name = name

		logging.debug("Get launcher entry %s", self.name)
		self.entry = Unity.LauncherEntry.get_for_desktop_id(self.name)

	def set_progress(self, progress):
		if progress is not None:
			self.entry.set_property('progress', progress)
			self.entry.set_property('progress_visible', True)
		else:
			self.entry.set_property('progress_visible', False)

	def set_count(self, count):
		if count is not None:
			self.entry.set_property('count', count)
			self.entry.set_property('count_visible', True)
		else:
			self.entry.set_property('count_visible', False)

	def set_quicklist_menu(self, menu):
		self.entry.set_property('quicklist', menu)


class QbittorrentUnityController:
    def __init__(self, qbittorrent, launcher_entry, options):
        self.qbittorrent = qbittorrent
        self.launcher_entry = launcher_entry
        self.options = options

        self.create_quicklist_menu()

    def update(self):
        logging.debug("Get torrents list.")
        torrents = self.qbittorrent.get_downloading_torrent_list()
      
        torrents_count = len(torrents)
        progress = self.qbittorrent.get_downloading_torrent_progress()        
        
        logging.debug("Recieved Downloading torrents count: %d", torrents_count)


        if torrents_count > 0:
            logging.info("Downloading torrents count: %d and progress %f", torrents_count, progress)
            # Set launcher entry properties.
            self.launcher_entry.set_count(torrents_count)
            self.launcher_entry.set_progress(progress)

        else:
            self.launcher_entry.set_count(None)
            self.launcher_entry.set_progress(None)

    def create_quicklist_menu(self):
        menu = Dbusmenu.Menuitem.new()
        pause_all_item = Dbusmenu.Menuitem.new()
        pause_all_item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        pause_all_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Pause All")
        self.pause_all_item = pause_all_item
        menu.child_append(pause_all_item)
        self.pause_all_item.property_set_bool(Dbusmenu.MENUITEM_PROP_VISIBLE, True)
        all_paused = self.qbittorrent.all_paused()
        logging.debug('All paused? %d', all_paused);
        if all_paused:
            self.pause_all_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Resume All")

        self.pause_all_item.connect('item-activated', self._on_menu_pause_all, None)        
        self.launcher_entry.set_quicklist_menu(menu)

    def _on_menu_pause_all(self, menuitem, _, data):
        current_state = menuitem.property_get(Dbusmenu.MENUITEM_PROP_LABEL)
        if current_state == 'Pause All':
            self.qbittorrent.pause_all()
            self.pause_all_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Resume All")
        else:
            self.qbittorrent.resume_all()
            self.pause_all_item.property_set(Dbusmenu.MENUITEM_PROP_LABEL, "Pause All")


logging.basicConfig(level=logging.WARNING)

parser = argparse.ArgumentParser(description="Integrate Qbittorrent into Unity Launcher.")
parser.add_argument('qbittorrent_command',
    nargs='+',
    help="Command and arguments to start qbittorrent")

parser.add_argument('-H', '--host',
    action='store', dest='host',
    default='localhost',
    help="address for connecting to Qbitorrent RPC")

parser.add_argument('-p', '--port',
    action='store', dest='port', type=int,
    default=8080,
    help="port for connecting to Qbittorrent RPC")

parser.add_argument('-U', '--user',
    action='store', dest='user',
    default=None,
    help="user name for connecting to Qbittorent RPC")

parser.add_argument('-P', '--password',
    action='store', dest='password',
    default=None,
    help="password for connecting to Qbittorrent RPC")

parser.add_argument('-u', '--update-interval',
	action='store', dest='update_interval', type=int,
	default=20,
	help="interval (in seconds) between status updates")

parser.add_argument('-t', '--startup-timeout',
	default=4,
	help="time (in seconds) between Qbittorrent start and first connection attempt")

parser.add_argument('-l', '--launcher-entry-name',
	action='store', dest='launcher_entry_name',
	default='qBittorrent.desktop',
	help="name of .desktop file (including extension) used to start Qbittorrent")


args = parser.parse_args()

loop = GObject.MainLoop()

def start_process(command):
    flags = (
        # Inherit PATH environment variable.
        GLib.SpawnFlags.SEARCH_PATH |

        # Don't reap process automatically so it is possible
        # to detect when it is closed.
        GLib.SpawnFlags.DO_NOT_REAP_CHILD
    )
    pid = spawn_async(command, flags)
    return pid

qbt_pid = start_process(args.qbittorrent_command)
logging.info("Qbittorrent started (pid: %d).", qbt_pid)

# Exit when Qbittorrent is closed.
def qbittorrent_closed(pid, status, data):
    logging.info("Qbittorrent exited with status %d, exiting.", status)
    GLib.spawn_close_pid(pid)
    loop.quit()

child_watch_add(GLib.PRIORITY_DEFAULT, qbt_pid, qbittorrent_closed, None)

def first_update():
    qbittorrent = qbittorrentrpc.Client(args.host, args.port, args.user, args.password)
    launcher_entry = UnityLauncherEntry(args.launcher_entry_name)
    # Create controller.
    controller = QbittorrentUnityController(qbittorrent, launcher_entry, args)
    # Try to update status for the first time.
    controller.update()
    # If all is ok, start main timer.
    GObject.timeout_add_seconds(args.update_interval, periodic_update, controller)


def periodic_update(controller):
    logging.debug('Periodic Update')
    try:
        controller.update()
    except:
        logging.error("Connection to Qbittorrent is lost.")
        sys.stderr.write("""Connection to Qbittorrent is lost. Quit.""")
        loop.quit() # Terminate application loop.

    GObject.timeout_add_seconds(args.update_interval, periodic_update, controller)
    

GObject.timeout_add_seconds(args.startup_timeout, first_update)

loop.run()
