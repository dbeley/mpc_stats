#! /usr/bin/enb python
import os
import errno
import csv
import logging
import time
import argparse
import configparser
import discogs_client
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger()
temps_debut = time.time()


def main():
    args = parse_args()
    config = configparser.RawConfigParser()
    config.read('config')
    user_token = config['discogs']['user_token']
    d = discogs_client.Client('mpc_stats/0.1', user_token=user_token)
    
    os.system("mpc list albumartist > albumartist.txt")
    with open("albumartist.txt", "r") as f:
        list_artists = [line.strip() for line in f if line.strip()]
    for artist in list_artists:
        artist = artist.rstrip()
        logger.debug(f"Querying albums for artist : {artist}")
        artist_filename = artist.replace("/", "-")
        filename = f"output/{artist_filename}.txt"
        if not os.path.exists(os.path.dirname(filename)):
            try:
                logger.debug(f"création du chemin pour {filename}")
                os.makedirs(os.path.dirname(filename))
            except OSError as exc:
                if exc.errno != errno.EEXIST:
                    raise
        os.system(f"mpc list album albumartist \"{artist}\" > \"{filename}\"")
    directory = "output"
    pathlist = Path(directory).glob('**/*.txt')
    pathlist_size = sum(1 for x in pathlist)
    pathlist = Path(directory).glob('**/*.txt')
    collection = []
    collection.append(
            [
                "Artist",
                "Album",
                "Year",
                "Country",
                "Genre"
            ]
            )

    for file in tqdm(sorted(pathlist), dynamic_ncols=True, total=pathlist_size):
        artist = os.path.basename(os.path.splitext(file)[0])
        logger.info(f"File : {file} - Artist : {artist}")
        with open(file, "r") as f:
            albums = f.readlines()
        for album in albums:
            album = album.rstrip()
            logger.debug(f"d.search({artist} - {album}, type='release')")
            try:
                results = search_discogs(d, artist, album)
                if (len(results) > 0):
                    year = results[0].year
                    country = results[0].country
                    genres = results[0].genres
                    logger.debug(f"{str(artist)} - {str(album)} - release date : {str(year)} - country : {str(country)} - genres : {str(genres)}")
                    collection.append([str(artist), str(album), str(year), str(country), str(genres)])
                else:
                    logger.warning(f"No release found for {str(artist)} - {str(album)}")
            except Exception as e:
                logger.error(e)

    with open("collection.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerows(collection)

    print("Runtime : %.2f seconds" % (time.time() - temps_debut))


def RateLimited(maxPerSecond):
    minInterval = 1.0 / float(maxPerSecond)

    def decorate(func):
        lastTimeCalled = [0.0]

        def rateLimitedFunction(*args, **kargs):
            elapsed = time.process_time() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait > 0:
                time.sleep(leftToWait)
            ret = func(*args, **kargs)
            lastTimeCalled[0] = time.process_time()
            return ret
        return rateLimitedFunction
    return decorate


@RateLimited(1)
def search_discogs(d, artist, album):
    return(d.search(f"{artist} - {album}", type='release'))


def parse_args():
    parser = argparse.ArgumentParser(description='Extract unique images from videos')
    parser.add_argument('--debug', help="Display debugging information", action="store_const", dest="loglevel", const=logging.DEBUG, default=logging.INFO)
    args = parser.parse_args()
    logging.basicConfig(level=args.loglevel)
    return args


if __name__ == '__main__':
    main()
