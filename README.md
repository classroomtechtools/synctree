# synctree
Framework for importing / exporting information between CSVs and databases

###CONTEXT

You're a school with a few providers in an organization. One of them is the source of truth for things like class enrollments and student data, and another open source tool like Google or Moodle. You want the information to one-way sync so you can manage other things.

Using this framework, you define the model for the source, and the targets(s). The framework takes those two models and finds the differences, sending it on to a template. The template code then does the necessary action to update the database.

###QUICKSTART

