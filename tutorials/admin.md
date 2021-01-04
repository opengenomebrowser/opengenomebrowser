<link rel="shortcut icon" type="image/svg+xml" href="/opengenomebrowser/favicon.svg">

# Admin panel

The admin panel enables specific users to change (some of) the metadata in the database:
  - create new tags and edit their descriptions
  - change the metadata associated with organisms (e.g.: change TaxId)<sup>*</sup>
  - change the metadata associated with genomes<sup>*</sup>

*: any changes are automatically propagated to the corresponding`genome.json` or `organism.json` and a backup is made.

In addition, superusers may create new user accounts.

Thus, experts without UNIX skills can easily change these things without having to bother the OpenGenomeBrowser system administrator.

![admin demo](../media/admin.apng)
