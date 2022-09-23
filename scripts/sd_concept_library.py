# base webui import and utils.
from webui_streamlit import st
from sd_utils import *

# streamlit imports
import streamlit.components.v1 as components


class plugin_info():
	plugname = "concept_library"
	description = "Concept Library"
	displayPriority = 4


# Init Vuejs component
_component_func = components.declare_component(
	"sd-concepts-browser", "./frontend/dist")


def sdConceptsBrowser(concepts, key=None):
	component_value = _component_func(concepts=concepts, key=key, default="")
	return component_value


@st.cache(persist=True, allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
def getConceptsFromPath(page, conceptPerPage, searchText=""):
	#print("getConceptsFromPath", "page:", page, "conceptPerPage:", conceptPerPage, "searchText:", searchText)
	# get the path where the concepts are stored
	path = os.path.join(
		os.getcwd(),  st.session_state['defaults'].general.sd_concepts_library_folder)
	acceptedExtensions = ('jpeg', 'jpg', "png")
	concepts = []

	if os.path.exists(path):
		# List all folders (concepts) in the path
		folders = [f for f in os.listdir(
			path) if os.path.isdir(os.path.join(path, f))]
		filteredFolders = folders

		# Filter the folders by the search text
		if searchText != "":
			filteredFolders = [
				f for f in folders if searchText.lower() in f.lower()]
	else:
		filteredFolders = []

	conceptIndex = 1
	for folder in filteredFolders:
		# handle pagination
		if conceptIndex > (page * conceptPerPage):
			continue
		if conceptIndex <= ((page - 1) * conceptPerPage):
			conceptIndex += 1
			continue

		concept = {
			"name": folder,
			"token": "<" + folder + ">",
			"images": [],
			"type": ""
		}

		# type of concept is inside type_of_concept.txt
		typePath = os.path.join(path, folder, "type_of_concept.txt")
		binFile = os.path.join(path, folder, "learned_embeds.bin")

		# Continue if the concept is not valid or the download has failed (no type_of_concept.txt or no binFile)
		if not os.path.exists(typePath) or not os.path.exists(binFile):
			continue

		with open(typePath, "r") as f:
			concept["type"] = f.read()

		# List all files in the concept/concept_images folder
		files = [f for f in os.listdir(os.path.join(path, folder, "concept_images")) if os.path.isfile(
			os.path.join(path, folder, "concept_images", f))]
		# Retrieve only the 4 first images
		for file in files[:4]:
			if file.endswith(acceptedExtensions):
				# Add a copy of the image to avoid file locking
				originalImage = Image.open(os.path.join(
					path, folder, "concept_images", file))

				# Maintain the aspect ratio (max 200x200)
				resizedImage = originalImage.copy()
				resizedImage.thumbnail((200, 200), Image.ANTIALIAS)

				# concept["images"].append(resizedImage)

				concept["images"].append(imageToBase64(resizedImage))
				# Close original image
				originalImage.close()

		concepts.append(concept)
		conceptIndex += 1
	# print all concepts name
	#print("Results:", [c["name"] for c in concepts])
	return concepts


@st.cache(persist=True, allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
def imageToBase64(image):
	import io
	import base64
	buffered = io.BytesIO()
	image.save(buffered, format="PNG")
	img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
	return img_str


@st.cache(persist=True, allow_output_mutation=True, show_spinner=False, suppress_st_warning=True)
def getTotalNumberOfConcepts(searchText=""):
	# get the path where the concepts are stored
	path = os.path.join(
		os.getcwd(),  st.session_state['defaults'].general.sd_concepts_library_folder)
	concepts = []

	if os.path.exists(path):
		# List all folders (concepts) in the path
		folders = [f for f in os.listdir(
			path) if os.path.isdir(os.path.join(path, f))]
		filteredFolders = folders

		# Filter the folders by the search text
		if searchText != "":
			filteredFolders = [
				f for f in folders if searchText.lower() in f.lower()]
	else:
		filteredFolders = []
	return len(filteredFolders)



def layout():
	# 2 tabs, one for Concept Library and one for the Download Manager
	tab_library, tab_downloader = st.tabs(["Library", "Download Manager"])

	# Concept Library
	with tab_library:
		downloaded_concepts_count = getTotalNumberOfConcepts()
		concepts_per_page = 12

		if not "results" in st.session_state:
			st.session_state["results"] = getConceptsFromPath(1, concepts_per_page, "")

		# Pagination controls
		if not "cl_current_page" in st.session_state:
			st.session_state["cl_current_page"] = 1

		# Search
		if not 'cl_search_text' in st.session_state:
			st.session_state["cl_search_text"] = ""

		if not 'cl_search_results_count' in st.session_state:
			st.session_state["cl_search_results_count"] = downloaded_concepts_count

		# Search bar
		search_text_input = st.text_input("", "", placeholder=f'Search for a concept ({downloaded_concepts_count} available)')
		if search_text_input != st.session_state["cl_search_text"]:
			# Search text has changed
			st.session_state["cl_search_text"] = search_text_input
			st.session_state["cl_current_page"] = 1
			st.session_state["cl_search_results_count"] = getTotalNumberOfConcepts(st.session_state["cl_search_text"])
			st.session_state["results"] = getConceptsFromPath(1, concepts_per_page, st.session_state["cl_search_text"])

		# Show results
		results_empty = st.empty()

		# Pagination
		pagination_empty = st.empty()

		# Layouts
		with pagination_empty:
			with st.container():
				if len(st.session_state["results"]) > 0:
					last_page = math.ceil(st.session_state["cl_search_results_count"] / concepts_per_page)
					_1, _2, _3, _4, _previous_page, _current_page, _next_page, _9, _10, _11, _12 = st.columns([1,1,1,1,1,2,1,1,1,1,1])

					# Previous page
					with _previous_page:
						if st.button("<", key="cl_previous_page"):
							st.session_state["cl_current_page"] -= 1
							if st.session_state["cl_current_page"] <= 0:
								st.session_state["cl_current_page"] = last_page
							st.session_state["results"] = getConceptsFromPath(st.session_state["cl_current_page"], concepts_per_page, st.session_state["cl_search_text"])

					# Current page
					with _current_page:
						_current_page_container = st.empty()

					# Next page
					with _next_page:
						if st.button(">", key="cl_next_page"):
							st.session_state["cl_current_page"] += 1
							if st.session_state["cl_current_page"] > last_page:
								st.session_state["cl_current_page"] = 1
							st.session_state["results"] = getConceptsFromPath(st.session_state["cl_current_page"], concepts_per_page, st.session_state["cl_search_text"])

					# Current page
					with _current_page_container:
						st.markdown(f'<p style="text-align: center">Page {st.session_state["cl_current_page"]} of {last_page}</p>', unsafe_allow_html=True)
						# st.write(f"Page {st.session_state['cl_current_page']} of {last_page}", key="cl_current_page")

		with results_empty:
			with st.container():
				if downloaded_concepts_count == 0:
					st.write("You don't have any concepts in your library ")
					st.markdown("To add concepts to your library, download some from the [sd-concepts-library](https://github.com/sd-webui/sd-concepts-library) \
						repository and save the content of `sd-concepts-library` into ```./models/custom/sd-concepts-library``` or just create your own concepts :wink:.", unsafe_allow_html=False)
				else:
					if len(st.session_state["results"]) == 0:
						st.write("No concept found in the library matching your search: " + st.session_state["cl_search_text"])
					else:
						# display number of results
						if st.session_state["cl_search_text"]:
							st.write(f"Found {st.session_state['cl_search_results_count']} {'concepts' if st.session_state['cl_search_results_count'] > 1 else 'concept' } matching your search")
						sdConceptsBrowser(st.session_state['results'], key="results")


	with tab_downloader:
		st.write("Not implemented yet")

	return False
