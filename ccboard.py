import jinja2
import os
import SocketServer
import sys

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

DEFAULT_PORT = 9487

class RequestHandler(BaseHTTPRequestHandler):
    def __init__(self, context, *args):
        self.context = context
        BaseHTTPRequestHandler.__init__(self, *args)

    def _set_headers(self, status_code, content_type):
        self.send_response(status_code)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def do_GET(self):
        try:
            if self.path.startswith('/static'):
                f = open('.' + self.path)
                if self.path.endswith('.css'):
                    self._set_headers(200, 'text/css')
                elif self.path.endswith('.js'):
                    self._set_headers(200, 'application/javascript')
                else:
                    self._set_headers(200, 'text/plain')
                self.wfile.write(f.read())
            else:
                self._set_headers(200, 'text/html')
                _str = jinja2.Environment(
                    loader = jinja2.FileSystemLoader('./')
                ).get_template('template.html').render(self.context)
                self.wfile.write(_str)

        except IOError:
            self.send_error(404, 'File not found: ' + self.path)

def handleRequestUsing(context):
    return lambda *args: RequestHandler(context, *args)

def run(context, port = DEFAULT_PORT):
    server_address = ('', port)
    handler = handleRequestUsing(context)
    httpd = HTTPServer(server_address, handler)
    print 'String CCBoard on port ' + str(port)
    httpd.serve_forever()

def get_formatted_metircs(dir_name, iou, precision, recall, f1_score):
    return {
        'dir': dir_name,
        'IoU': iou,
        'precision': precision,
        'recall': recall,
        'F1 score': f1_score
    }

def average_formatted_metrics(formatted_metrics, count):
    formatted_metrics['IoU'] /= count
    formatted_metrics['precision'] /= count
    formatted_metrics['recall'] /= count
    formatted_metrics['F1 score'] /= count

def get_context(root_dir):
    # Get all classification folders
    class_dirs = os.listdir(root_dir)
    class_dirs.sort()

    # Initialize classes metrics
    classes_metrics = []
    all_formatted_metrics = get_formatted_metircs('AVERAGE', 0.0, 0.0, 0.0, 0.0)
    all_count = int(0)

    # Loop over classification folders
    for class_dir in class_dirs:
        # Get all sub folders in the classification folder
        class_dir_path = root_dir + '/' + class_dir
        sub_dirs = os.listdir(class_dir_path)

        # Initialize class metrics
        class_metrics = []
        class_formatted_metrics = get_formatted_metircs('AVERAGE', 0.0, 0.0, 0.0, 0.0)

        # Loop over sub folders and get metrics
        for sub_dir in sub_dirs:
            dir_path = class_dir_path + '/' + sub_dir
            metrics = open(dir_path + '/metrics.txt').read().split('\n')
            formatted_metrics = get_formatted_metircs(sub_dir, 0.0, 0.0, 0.0, 0.0)
            for metric in metrics:
                if metric != '':
                    name = metric.split(': ')[0]
                    value = float(metric.split(': ')[1])
                    if name == 'IoU':
                        formatted_metrics['IoU'] = value
                        class_formatted_metrics['IoU'] += value
                        all_formatted_metrics['IoU'] += value
                    elif name == 'precision':
                        formatted_metrics['precision'] = value
                        class_formatted_metrics['precision'] += value
                        all_formatted_metrics['precision'] += value
                    elif name == 'recall':
                        formatted_metrics['recall'] = value
                        class_formatted_metrics['recall'] += value
                        all_formatted_metrics['recall'] += value
                    elif name == 'F1 score':
                        formatted_metrics['F1 score'] = value
                        class_formatted_metrics['F1 score'] += value
                        all_formatted_metrics['F1 score'] += value
            class_metrics.append(formatted_metrics)

        # Update metrics about the classification
        count = len(sub_dirs)
        average_formatted_metrics(class_formatted_metrics, count)
        class_metrics = [class_formatted_metrics] + class_metrics;
        classes_metrics.append({
            'class_dir': class_dir,
            'metrics_list': class_metrics
        })
        # Update the total count
        all_count += count

    # Update the overall metrics
    average_formatted_metrics(all_formatted_metrics, all_count)
    classes_metrics = [{
        'class_dir': 'OVERALL',
        'metrics_list': [all_formatted_metrics]
    }] + classes_metrics

    return {
        'root_dir': root_dir,
        'classes_metrics': classes_metrics
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python ' + sys.argv[0] + ' folder [port]')
        sys.exit(-1)

    context = get_context(sys.argv[1])

    if len(sys.argv) >= 3:
        run(context, port = int(argv[2]))
    else:
        run(context)
