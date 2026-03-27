import { loadResource } from "../../static/utils/resources.js";

export default {
  template: "<div></div>",
  props: {
    options: Array,
    custom_css: String,
    resourcePath: String,
  },
  async mounted() {
    // wait for window.path_prefix to be set
    await this.$nextTick(); 
    await loadResource(window.path_prefix + `${this.resourcePath}/index.global.min.js`);
    this.options.eventClick = (info) => this.$emit("click", { info });
    // see: https://fullcalendar.io/docs/datesSet
    this.options.datesSet = (info) => this.$emit("change", { info });
    this.calendar = new FullCalendar.Calendar(this.$el, this.options);
    this.calendar.render();
  },
  methods: {
    update_calendar() {
      if (this.calendar) {
        // set events for JS calendar with data from Python
        this.calendar.setOption("events", this.options.events);
        // apply custom css if provided
        if (this.custom_css) {
          const style = document.createElement('style');
          style.innerHTML = this.custom_css;
          document.head.appendChild(style);
        }
        this.calendar.render();
      }
    },
  },
};
