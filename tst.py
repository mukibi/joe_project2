movies = read_entire_catalogue()

if ( title_filtered ):
	movies = filter_by_info(movies, "title", title )
if ( filename_filtered ):
	movies = filter_by_info(movies, "filename", filename )
if ( year_filtered ):
	movies = filter(movies, "year", year)

if (crew_filtered ):
	movies = filter_by_crew(movies, crews_list, search_crew) 

filter_by_info(movie_list, field, search_value):

	for movie_id in movie_list:

		if ( not movie_list[movie_id][field].find(search_value) >= 0 ):
			movie_list.pop(movie_id)

	return movie_list

			
filter_by_crew(movie_list, crews_list, search_crew_member_name):

	for movie_id in movie_list:
		for crew_movie_id in crews_list:
			if (crew_movie_id == movie_id):
				for crew_member in crews_list[crew_movie_id]:
					if ( not crews_list[crew_movie_id][crew_member]["name"].find(search_crew_member_name) >= 0 ):
						movie_list.pop(movie_id)

	return movie_list


