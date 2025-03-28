User Guide
==========

This section provides detailed instructions for using the BSTI Nessus to Plextrac converter.

.. toctree::
   :maxdepth: 2

   installation
   configuration
   converting
   uploading
   advanced

Basic Usage
-----------

The BSTI Nessus converter is designed to be straightforward to use. Here's a quick overview:

1. Install the package (see :doc:`installation`)
2. Run the configuration wizard to set up your preferences:

   .. code-block:: bash
   
      bsti-nessus --config-wizard

3. Convert a Nessus CSV file to Plextrac format:

   .. code-block:: bash
   
      bsti-nessus convert path/to/nessus_file.csv

4. Upload findings to Plextrac:

   .. code-block:: bash
   
      bsti-nessus upload path/to/converted_findings.json

For more detailed instructions on each step, please refer to the relevant sections of this user guide. 