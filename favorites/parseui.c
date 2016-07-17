#include "parseui.xml.ch"
#include "squeetie.png.ch"
#include "sweetie_thinking.png.ch"

#define CLOSURE(name) typedef struct name ## _s { \
		name ## _f cb; \ 
		void* data; \
	} *name

typedef void (*Clicked_f)(void*, GdkEventType, guint, guint);
typedef void (*Destroyed_f)(void*);
CLOSURE(Clicked);
CLOSURE(Destroyed);

#define make_closure(name,cb,data) { name c = g_new(name ## _s, 1); \
		c->cb = cb; \
		c->data = data; \
		(void*)c;				\
	}


static void button_clicked(GtkWidget* widget, GdkEventButton* event, gpointer udata) {
	Clicked on_clicked = (Clicked) udata;
	on_clicked->cb(on_clicked->data,
								 event->type, event->state, event->button);
}

static void destroyed(GtkWidget* widget, void* udata) {
	Destroyed on_destroyed = (Destroyed) udata;
	on_destroyed->cb(on_destroyed->data);
}

typedef struct ui {
	GtkImage* img;
	GdkPixbufAnimation* ready;
	GdkPixbufAnimation* thinking;
}

static GtkAnimation* load_icon(gchar* buf, gsize len) {
	GdkPixbufLoader* loader = gdk_pixbuf_loader_new();
	gdk_pixbuf_loader_set_size(loader, 32, 32);
	GError* error = NULL;
	gdk_pixbuf_loader_write(buf,len,&error);
	assert(error==NULL);
	gdk_pixbuf_loader_close(loader,&error);
	GtkAnimation* anim = gdk_pixbuf_loader_get_animation(loader);
	g_object_unref(loader);
	return anim;
}

ui parseui_load(Clicked_f on_clicked,
								Destroyed_f on_destroyed,
								void* data) {
	GtkBuilder* b = gtk_builder_new_from_string(parseui, parseui_size);
	GtkWidget* top = GTK_WIDGET(gtk_builder_get_object(b,"top"));
	g_signal_connect(top, "button_release_event", button_clicked,
									 make_closure(Clicked, on_clicked, data));
	g_signal_connect(top, "destroy", destroyed,
									 make_closure(Destroyed, on_destroyed, data));
	gtk_widget_show_all(top);
	ui ui = g_new(struct ui, 1);
	ui->img = GTK_IMAGE(gtk_builder_get_object(b,"image"));
	ui->ready = load_icon(squeetie,squeetie_size);
	ui->thinking = load_icon(sweetie_think, sweetie_think_size);

	return ui;
}

enum states { READY = 0, THINKING = 1 };

void parseui_state(ui ui, enum states state) {
	switch(state) {
	#define CASE(name,mem) \
		case name: \
			gtk_image_set_from_animation \
				(ui->img, \
				 gdk_pixbuf_loader_get_animation(ui->mem)); \
			break
		CASE(READY,ready);
		CASE(THINKING,thinking);
	};
}
