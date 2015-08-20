import dashi.config
import jinja2
import os

def go():
    config = dashi.config.parse()
    template_loader = jinja2.FileSystemLoader(searchpath=config.template_path)
    template_environment = jinja2.Environment(loader=template_loader)
    template = template_environment.get_template('index.html')
    output = template.render()

    try:
        os.mkdir(config.output_path)
    except OSError:
        pass

    path = os.path.join(config.output_path, 'index.html')
    with open(path, 'w') as f:
        f.write(output)
