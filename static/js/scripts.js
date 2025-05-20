// Main JavaScript file for Tour Van Booking

document.addEventListener("DOMContentLoaded", function () {
  // Add fade-in animation to all cards
  const cards = document.querySelectorAll(".card");
  cards.forEach((card, index) => {
    card.style.animationDelay = `${index * 0.1}s`;
    card.classList.add("fade-in");
  });

  // Validate date inputs for booking form
  const startDateInput = document.getElementById("start_date");
  const endDateInput = document.getElementById("end_date");
  const priceDisplay = document.getElementById("price_display");
  const vanPriceInput = document.getElementById("van_price");

  if (startDateInput && endDateInput) {
    // Set min date to today
    const today = new Date().toISOString().split("T")[0];
    startDateInput.min = today;

    // Update end date min when start date changes
    startDateInput.addEventListener("change", function () {
      endDateInput.min = startDateInput.value;

      // If end date is before start date, reset it
      if (endDateInput.value && endDateInput.value < startDateInput.value) {
        endDateInput.value = startDateInput.value;
      }

      updateTotalPrice();
    });

    // Update price when end date changes
    endDateInput.addEventListener("change", updateTotalPrice);
  }

  // Function to update total price
  function updateTotalPrice() {
    if (startDateInput && endDateInput && priceDisplay && vanPriceInput) {
      if (startDateInput.value && endDateInput.value) {
        const start = new Date(startDateInput.value);
        const end = new Date(endDateInput.value);
        const days = Math.max(
          1,
          Math.ceil((end - start) / (1000 * 60 * 60 * 24))
        );
        const pricePerDay = parseInt(vanPriceInput.value);
        const totalPrice = days * pricePerDay;

        priceDisplay.textContent = `$${totalPrice}`;
        document.getElementById("total_price").value = totalPrice;
      }
    }
  }

  // Form validation with visual feedback
  const forms = document.querySelectorAll("form");
  forms.forEach((form) => {
    form.addEventListener("submit", function (event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();

        // Add shake animation to invalid fields
        const invalidFields = form.querySelectorAll(":invalid");
        invalidFields.forEach((field) => {
          field.classList.add("shake");
          setTimeout(() => field.classList.remove("shake"), 500);
        });
      }

      form.classList.add("was-validated");
    });
  });

  // Add loading indicator for form submissions
  forms.forEach((form) => {
    form.addEventListener("submit", function () {
      if (form.checkValidity()) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          const originalText = submitBtn.innerHTML;
          submitBtn.innerHTML =
            '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span> Processing...';
          submitBtn.disabled = true;

          // Re-enable after 10 seconds in case of network issues
          setTimeout(() => {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
          }, 10000);
        }
      }
    });
  });

  // Initialize tooltips
  const tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });
});
