document.addEventListener("DOMContentLoaded", function () {
  // Date validation
  const startDate = document.getElementById("start_date");
  const endDate = document.getElementById("end_date");

  if (startDate && endDate) {
    startDate.min = new Date().toISOString().split("T")[0];

    startDate.addEventListener("change", function () {
      endDate.min = this.value;
      if (endDate.value && endDate.value < this.value) {
        endDate.value = this.value;
      }
    });
  }
});
