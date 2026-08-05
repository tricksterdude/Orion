from app.metadata.tmdb_manager import TMDbManager


tmdb = TMDbManager()

movie = tmdb.lookup_imdb("tt0133093")

print("=" * 60)
print("MOVIE METADATA")
print("=" * 60)

print()

print("IMDb :", movie.imdb_id)
print("TMDb :", movie.tmdb_id)

print()

print("Title :", movie.title)
print("Year  :", movie.year)

print()

print("Rating :", movie.vote_average)

print()

print("Poster")

print(movie.poster)

print()

print("Backdrop")

print(movie.backdrop)