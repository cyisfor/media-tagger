#include "parseui.xml.ch"
#include "squeetie.png.ch"
#include "sweetie_thinking.gif.ch"

#include <gtk/gtk.h>
#include <assert.h>
#include <python.h>

void ignore_result(PyObject* result) {
	assert(result != NULL); Py_DECREF(result);
}

static void button_clicked(GtkWidget* widget, GdkEventButton* event,
													 PyObject* on_clicked) {
	PyObject* arglist = Py_BuildValue
		("(iii)",
		 event->type, event->state, event->button);
	ignore_result(PyObject_CallObject(on_clicked, arglist));
	Py_DECREF(arglist);
}

PyObject* Py_Empty = NULL;

static void destroyed(GtkWidget* widget,
											PyObject* on_destroyed) {
	PyObject* arglist = Py_BuildValue("()");
	ignore_result(PyObject_CallObject(on_destroyed,Py_Empty));
}

typedef struct ui {
	GtkImage* img;
	GdkPixbufAnimation* ready;
	GdkPixbufAnimation* thinking;
} *ui;

static GdkPixbufAnimation* load_icon(gchar* buf, gsize len) {
	GdkPixbufLoader* loader = gdk_pixbuf_loader_new();
	gdk_pixbuf_loader_set_size(loader, 32, 32);
	GError* error = NULL;
	gdk_pixbuf_loader_write(loader, buf,len,&error);
	assert(error==NULL);
	gdk_pixbuf_loader_close(loader,&error);
	GdkPixbufAnimation* anim = gdk_pixbuf_loader_get_animation(loader);
	g_object_unref(loader);
	return anim;
}

ui parseui_load(Clicked_f on_clicked,
								Destroyed_f on_destroyed,
								void* data) {
	if(Py_Empty == NULL) {
		Py_Empty = Py_BuildValue("()");
	}
	GtkBuilder* b = gtk_builder_new_from_string(parseui, parseui_size);
	GtkWidget* top = GTK_WIDGET(gtk_builder_get_object(b,"top"));
	g_signal_connect(top, "button_release_event", (GCallback)button_clicked,
									 make_closure(Clicked, on_clicked, data));
	g_signal_connect(top, "destroy", (GCallback)destroyed,
									 make_closure(Destroyed, on_destroyed, data));
	gtk_widget_show_all(top);
	ui ui = g_new(struct ui, 1);
	ui->img = GTK_IMAGE(gtk_builder_get_object(b,"image"));
	ui->ready = load_icon(squeetie,squeetie_size);
	ui->thinking = load_icon(sweetie_thinking, sweetie_thinking_size);

	return ui;
}

enum states { READY = 0, THINKING = 1 };

void parseui_state(ui ui, enum states state) {
	switch(state) {
	#define CASE(name,mem) \
		case name: \
			gtk_image_set_from_animation \
				(ui->img, \
				 ui->mem); \
			break
		CASE(READY,ready);
		CASE(THINKING,thinking);
	};
}
