import setuptools

setuptools.setup(
    name='fockes_reasoner',
    version='0.2',
    description='Reasoner that implements interpreter for RIF',
    #long_description="""This module should allow rdflib to load rif.""",
    long_description_content_type="text/markdown",

    # url="https://example.com/rif-parser-rdflib",
    
    author='Richard Focke Fechner',
    author_email='richardfechner@posteo.net',

    py_modules=['fockes_reasoner'],
    #scripts = ['rif_parser.py',],

    packages=setuptools.find_packages(),
    install_requires=['rdflib'],
    
    # Classifiers allow your Package to be categorized based on functionality
    classifiers = [
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],

    extras_require = {
        'rif_interpreter': ["rdflib_rif"],
        'time_builtins':  ['isodate>0.6.1'],
    },
)
