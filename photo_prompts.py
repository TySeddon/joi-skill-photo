from pprint import pprint
from google_photo import GooglePhoto
from nlp import NLP
from dialog import Dialog
import webbrowser

# test
photo_client = GooglePhoto()

albums = photo_client.get_albums()
album = list(filter(lambda o: o.title == "Joi", albums))[0]

mediaItems = photo_client.get_media_items(album_id=album.id)
print('===Getting Media Items=============')
for o in mediaItems:
    if o.description:
        print(o.description)

print('===Composing Prompts=============')
kb_project = 'joi-ruth'
nlp = NLP(kb_project)

dialog = Dialog(nlp, 'Ruth')

""" for o in mediaItems:
    if o.description:
        prompts = dialog.compose_prompts(o.description)
        print(f"===== {o.description} ==========")
        print(f"{o.baseUrl}")
        for p in prompts:
            if not hasattr(p, 'prompt'):
                print(p)
                quit()
            else:                
                print(f"{p.prompt}, ({p.confidence}), {p.source}") """

# html report
report_file_name = 'report.html'
with open(report_file_name, 'w') as f:
    f.write("<html>")
    f.write("<head><style>")
    f.write("table {border-collapse: collapse;}")
    f.write("th,td {text-align:left;padding:5px;font-size:9pt;}")
    f.write("tr:nth-child(even) {background-color: #dddddd;}")
    f.write("</style></head>")
    f.write("<body>")
    for o in mediaItems:
        if o.description:
            prompts = dialog.compose_prompts(o.description)
            f.write("<div style='margin:20px; clear:both; border-style: solid; padding:20px;page-break-after:always;'>")
            
            f.write("<div style='display:inline-block; margin-right:10px;'>")
            f.write(f"<img src='{o.baseUrl}' style='max-width:200px;'/>")
            f.write(f"<div style='font-size:20pt; max-width:200px;'>{o.description}</div>")
            f.write("</div>")

            f.write("<table style='display:inline-block; vertical-align:top;max-width:600px;'>")
            f.write("<tr> <th>Conversation Prompt</th> <th>Entity</th>  <th>Category</th>  <th>SubCat</th>  <th>Confidence</th> <th>Source</th> </tr>")
            for p in prompts:
                f.write("<tr>")
                f.write(f"<td>{p.prompt}</td>")
                f.write(f"<td>{p.entity_text}</td>")
                f.write(f"<td>{p.category}</td>")
                f.write(f"<td>{p.subcategory}</td>")
                f.write(f"<td>{int(round(p.confidence,2) * 100)}%</td>")
                f.write(f"<td>{p.source}</td>")
                f.write("</tr>")
            f.write("</table>")

            f.write("</div>")
    f.write("</body></html>")

webbrowser.open(report_file_name)