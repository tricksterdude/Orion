import requests

from app.config_manager import ConfigManager
from app.metadata.models import MovieMetadata


class TMDbManager:

    IMAGE_BASE = "https://image.tmdb.org/t/p/original"

    def __init__(self):

        config = ConfigManager()

        self.api_key = config.get("tmdb.api_key")

    def analyse(self, context):

        media = context.media

        if not media.imdb_id:

            return context

        metadata = self.lookup_imdb(media.imdb_id)

        if metadata:

            context.metadata = metadata

        return context

    def lookup_imdb(self, imdb_id):

        if not self.api_key:
            return None

        url = (
            f"https://api.themoviedb.org/3/find/{imdb_id}"
            f"?api_key={self.api_key}"
            "&external_source=imdb_id"
        )

        response = requests.get(url, timeout=10)

        response.raise_for_status()

        data = response.json()

        results = data.get("movie_results")

        if not results:
            return None

        movie = results[0]

        metadata = MovieMetadata()

        metadata.imdb_id = imdb_id
        metadata.tmdb_id = movie["id"]

        metadata.title = movie["title"]
        metadata.original_title = movie["original_title"]

        if movie.get("release_date"):
            metadata.year = int(movie["release_date"][:4])

        metadata.overview = movie.get("overview", "")

        metadata.vote_average = movie.get("vote_average", 0)

        metadata.poster = (
            self.IMAGE_BASE + movie["poster_path"]
            if movie.get("poster_path")
            else ""
        )

        metadata.backdrop = (
            self.IMAGE_BASE + movie["backdrop_path"]
            if movie.get("backdrop_path")
            else ""
        )

        metadata.media_type = movie.get("media_type", "movie")

        return metadata
