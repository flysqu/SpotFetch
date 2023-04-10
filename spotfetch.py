import tkinter as tk
from tkinter import filedialog
from io import BytesIO
from tkinter import messagebox
import requests
import json
from pytube import YouTube
from youtube_search import YoutubeSearch
from mutagen.id3 import ID3, APIC, TIT2
import os
from tkinter import font as tkfont
import time
from requests import get
from PIL import Image
from time import sleep

# Function to disable and remove the selected item from the listbox and list variable
def remove_item():
    selected_item = listbox.curselection() # Get the currently selected item in the listbox
    if selected_item: # If there is a selected item
        listbox.delete(selected_item) # Delete the selected item from the listbox

def add_items_to_list(listbox, oauth, playlist_id, offset):
    items = listbox.get(0, tk.END) # Get all items in the ListBox
    items_list = list(items) # Convert items to a list

    backendsonglist = getbackendsonglist(oauth, playlist_id, offset) # Call a function to get a backend song list

    newlist = [] # Initialize an empty list for new items

    for z in items_list: # Iterate through the items in the listbox
        for x in backendsonglist: # Iterate through the backend song list
            name = f"{x[1]}: {x[0]}" # Create a name string for each backend song
            if name == z: # If the name of the backend song matches the item in the listbox
                newlist.append(x) # Append the backend song to the new list

    print(newlist) # Print the new list (for debugging)
    return newlist # Return the new list

def addsongstolist(songlist):
    # Ensures that list is empty before adding songs to list
    listbox.delete(0, tk.END) # Delete all items in the listbox

    for song in songlist: # Iterate through the song list
        listbox.insert(tk.END, f"{song[1]}: {song[0]}") # Insert each song into the listbox with a formatted string

def getsonglist(oauth, playlist_id, offset):
    print("Starting to get songs from Spotify")

    # Build the URL for fetching playlist data from Spotify API
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track)&limit=100&offset={offset}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {oauth}"
    }

    print("Fetching playlist data from Spotify API...")
    response = requests.get(url, headers=headers) # Send GET request to Spotify API
    if response.status_code != 200:
        messagebox.showerror("Error", "Failed to fetch playlist data from Spotify API.")
        return

    print("Playlist data fetched successfully!")

    songlist = [] # Initialize an empty list for storing song data

    data = json.loads(response.text) # Parse response data as JSON

    if "items" not in data: # Check if "items" key exists in response data
        messagebox.showerror("Error", "Failed to parse playlist data from Spotify API.")
        return

    print(f"Total songs in playlist: {len(data['items'])}")

    for item in data["items"]: # Iterate through each item in the "items" key
        try:
            # Extract song name, artist name, and image URL from the item
            song = item['track']['name']
            artist = item['track']['artists'][0]['name']
            imgurl = item['track']['album']['images'][0]['url']

            songartist = (song, artist, imgurl) # Create a tuple with song, artist, and image URL
            songlist.append(songartist) # Append the tuple to the songlist
        except IndexError:
            # Catch IndexError that may occur when getting metadata for a song, show warning and continue
            messagebox.showwarning("Song Failed", f"Something went wrong with getting metadata. Will continue after closing warning. All songs may be working, Some may be missing")

    print("Fetching YouTube links for songs...")

    addsongstolist(songlist) # Call a function to add the songs to the listbox

def getbackendsonglist(oauth, playlist_id, offset):
    
    print("Starting to get songs from Spotify")
    
    # Construct URL for Spotify API endpoint
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks?fields=items(track)&limit=100&offset={offset}"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {oauth}"
    }

    print(f"Fetching playlist data from Spotify API...")
    
    # Fetch playlist data from Spotify API
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        messagebox.showerror("Error", "Failed to fetch playlist data from Spotify API.")
        return

    print(f"Playlist data fetched successfully!")
    
    songlist = []  # Initialize an empty list to store song metadata
    
    data = json.loads(response.text)  # Load response data as JSON
    
    if "items" not in data:
        messagebox.showerror("Error", "Failed to parse playlist data from Spotify API.")
        return

    print(f"Total songs in playlist: {len(data['items'])}")

    # Loop through each song item and extract metadata
    for item in data["items"]:
        try:
            song = item['track']['name']
            artist = item['track']['artists'][0]['name']
            imgurl = item['track']['album']['images'][0]['url']
            albumname = item['track']['album']['name']
            releasedate = item['track']['album']['release_date']

            # Create a tuple of song metadata and append to the songlist
            songartist = (song, artist, imgurl, albumname, releasedate)
            songlist.append(songartist)
        except IndexError:
            messagebox.showwarning("Song Failed", f"Something went wrong with getting the metadata from a song. Will continue after closing")
            time.sleep(0.5)

    return songlist  # Return the list of song metadata

def downsong(songs, output):
    # Concatenate song name and artist name to form the search query
    searchsong = f"{songs[1]}: {songs[0]}"
    
    # Search for the song on YouTube and retrieve the search results as JSON
    searchres = YoutubeSearch(searchsong, max_results=1).to_json()

    # Update the GUI (assuming there is a tkinter root window) to keep it responsive
    root.update()
    root.update_idletasks()

    # Parse the JSON data
    searchdata = json.loads(searchres)
    
    # Get the YouTube video ID of the first search result
    songid = searchdata['videos'][0]['id']

    try:
        # Create a filename for the downloaded song by replacing special characters
        songfilename = searchsong.replace("/", "").replace("*", "").replace("?", "").replace('"', "")

        # Filter for audio-only streams and download the song in mp3 format
        allaudiostreams = YouTube(f"https://youtu.be/{songid}").streams.filter(only_audio=True)
        songfilename = searchsong.replace("/","").replace("*", "").replace("?","").replace('"', "")
        YouTube(f"https://youtu.be/{songid}").streams.get_by_itag(140).download(output_path=f"{output}", filename=f"{songfilename}.mp3")
    except KeyError:
        # If the song is not found, print an error message and return False
        songfilename = searchsong.replace("/", "").replace("*", "").replace("?", "").replace('"', "")
        print(f"Song not found: {searchsong}")
        return False

    # Update the GUI
    root.update()
    root.update_idletasks()

    print(f"Fetching album art for: {searchsong}")

    # Make a GET request to retrieve the album art image data
    response = requests.get(songs[2])
    sleep(2)

    # Update the GUI
    root.update()
    root.update_idletasks()

    # Open the image using Pillow
    image = Image.open(BytesIO(response.content))

    # Save the image to disk using the song's filename
    art_path = f"{output}/{songfilename}.jpg"
    image.save(art_path)

    mp3_path = f"{output}/{songfilename}.mp3"

    # Update the GUI
    root.update()
    root.update_idletasks()

    try:
        # Try to load the ID3 tags from the downloaded mp3 file
        id3 = ID3(mp3_path)
    except:
        # If the file does not have ID3 tags, create a new ID3 object
        id3 = ID3()

    # Load the album art image file
    with open(art_path, 'rb') as f:
        art_data = f.read()

    # Create an APIC (Attached Picture) frame with the album art data
    apic = APIC(mime='image/jpeg', type=3, desc=u'Cover', data=art_data)

    # Update the GUI
    root.update()
    root.update_idletasks()

    # Add the APIC frame to the ID3 tags
    id3.add(apic)

    # Add the song title to the ID3 tags
    id3.add(TIT2(encoding=3, text=songs[0]))

    # Save the ID3 tags back to the .mp3 file
    id3.save(mp3_path)

    # Add more general tags using EasyID3
    from mutagen.easyid3 import EasyID3
    audio = EasyID3(mp3_path)

    audio["title"] = songs[0]
    audio["artist"] = songs[1]
    audio["album"] = songs[3]
    audio["date"] = songs[4]
    audio["originaldate"] = songs[4]
    audio.save()

    root.update()
    root.update_idletasks()


    os.remove(art_path)

    print(f"Song: {searchsong}, Has finished downloading")

    return True


def downsongs(output, oauth, playlist_id, offset):
    # Retrieve the list of songs from the playlist using the add_items_to_list function
    songlist = add_items_to_list(listbox, oauth, playlist_id, offset)
    
    # Show an information message box to notify the user about potential slowness of the interface
    messagebox.showinfo(message="The interface will be pretty slow but it does update so be patient (0.5s - 1s) when scrolling through the listbox")

    # Initialize a counter variable
    i = 0
    
    # Loop through each song in the songlist
    for songs in songlist:
        # Update the foreground color of the current item in the listbox to yellow
        listbox.itemconfigure(i, fg="yellow")
        root.update()
        root.update_idletasks()
        
        # Call the downsong function to download the current song
        trufal = downsong(songs, output)

        # Check the return value of the downsong function
        if trufal == False:
            # If the song was not found on YouTube, show a warning message box
            messagebox.showwarning(message=f"Song was not found on YouTube: {songs[0]}")
            time.sleep(0.5)

            # Scroll down by 1 unit in the listbox
            listbox.yview_scroll(1, tk.UNITS)
            # Update the foreground color of the current item in the listbox to yellow
            listbox.itemconfigure(i, fg="yellow")
            root.update()
            root.update_idletasks()
        else:
            # If the song was downloaded successfully, update the foreground color of the current item in the listbox to green
            listbox.itemconfigure(i, fg="green")
            root.update()
            root.update_idletasks()

        # Increment the counter variable
        i += 1

    # Print a message indicating that all songs were downloaded successfully
    print("All songs downloaded successfully!")


def browse_folder():
    from tkinter import messagebox
    folder_path = filedialog.askdirectory()
    output_entry.delete(0, tk.END)
    output_entry.insert(tk.END, folder_path)

root = tk.Tk()
root.title("Spotify Playlist Downloader")

playlist_id_label = tk.Label(root, text="Playlist ID:")
playlist_id_label.grid(row=0, column=0, padx=10, pady=10)
playlist_id_entry = tk.Entry(root)
playlist_id_entry.grid(row=0, column=1, padx=10, pady=10)

oauth_label = tk.Label(root, text="OAuth Token:")
oauth_label.grid(row=1, column=0, padx=10, pady=10)
oauth_entry = tk.Entry(root)
oauth_entry.grid(row=1, column=1, padx=10, pady=10)

offset_label = tk.Label(root, text="Offset:")
offset_label.grid(row=2, column=0, padx=10, pady=10)
offset_entry = tk.Entry(root)
offset_entry.grid(row=2, column=1, padx=10, pady=10)


output_label = tk.Label(root, text="Output Directory:")
output_label.grid(row=3, column=0, padx=10, pady=10)
output_entry = tk.Entry(root)
output_entry.grid(row=3, column=1, padx=10, pady=10)
output_button = tk.Button(root, text="Browse", command=lambda: output_entry.insert(0, filedialog.askdirectory()))
output_button.grid(row=3, column=2, padx=10, pady=10)

listsongs_button = tk.Button(root, text="List Songs", command=lambda: getsonglist(oauth=oauth_entry.get(), playlist_id=playlist_id_entry.get(), offset=offset_entry.get()))
listsongs_button.grid(row=6, column=1, padx=10, pady=10)

# Create listbox
listbox = tk.Listbox(root, selectmode=tk.SINGLE)
listbox.grid(row=7, column=1, padx=10, pady=10, sticky=tk.N+tk.S+tk.W+tk.E)


remove_button = tk.Button(root, text="Remove", command=remove_item)
remove_button.grid(row=8, column=1, padx=10, pady=2)

download_button = tk.Button(root, text="Download Songs", command=lambda: downsongs(output_entry.get(), oauth_entry.get(), playlist_id_entry.get(), offset_entry.get()))
download_button.grid(row=9, column=1, padx=10, pady=10)

root.mainloop()