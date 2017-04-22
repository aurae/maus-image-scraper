from flask import Flask, request, jsonify
from werkzeug.exceptions import HTTPException
from werkzeug.http import HTTP_STATUS_CODES
import jsonschema

import config
from app.models.objects import ScrapeRequest, ImageFormat

# Setup application object

app = Flask(__name__)
app.config.from_object(config)

app.scraper = app.config["SCRAPER_IMPL"]
""" :type: models.objects.Scraper """

# Setup error handling


def error_handler(error):
    app.log_exception(error)

    if isinstance(error, HTTPException):
        http_code = error.code
    elif isinstance(error, jsonschema.ValidationError):
        http_code = 400
    else:
        http_code = 500

    http_msg = HTTP_STATUS_CODES.get(http_code, "Bad Request")

    return jsonify({
        "code": http_code,
        "message": http_msg
    }), http_code

all_exception_types = HTTPException.__subclasses__() + [jsonschema.ValidationError, Exception]
for exc_type in all_exception_types:
    app.register_error_handler(exc_type, error_handler)

# Setup API endpoints for content delivery


@app.route("/images", methods=["POST"])
def search_images():
    # Validate request
    inputs = request.json
    jsonschema.validate(inputs, {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
            },
            "format": {
                "enum": ImageFormat.values(),
            },
            "page": {
                "type": "integer"
            }
        },
        "required": ["query"],
    })

    # Extract request parameters
    search_query = inputs["query"]
    search_format = ImageFormat(inputs["format"]) if "format" in inputs else None
    search_page = inputs.get("page", 1)

    # Perform request
    image_request = ScrapeRequest(
        query=search_query,
        image_format=search_format,
        page=search_page
    )
    image_response = app.scraper.scrape_images(image_request)

    # Format response
    return jsonify({
        "results": [
            {
                "url": image.full_url,
                "thumbnail": image.thumb_url,
                "description": image.description,
                "width": image.width,
                "height": image.height
            }
            for image in image_response.results
        ]
    })
