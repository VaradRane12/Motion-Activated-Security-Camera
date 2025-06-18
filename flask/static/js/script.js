
let liveFeedActive = false;
let lightArmed = false;
let sirenArmed = false;
// === INIT ON LOAD ===
document.addEventListener("DOMContentLoaded", function () {
    if (surveillance_state === "paused") {
        pauseSurveillanceUIOnly();
    } else {
        resumeSurveillanceUIOnly();
    }
    console.log(lightStatus)
    if (lightStatus === "ON") {
    document.getElementById("turnonlight").style.display = "none";
    document.getElementById("turnofflight").style.display = "block";
    } else {
        document.getElementById("turnonlight").style.display = "block";
        document.getElementById("turnofflight").style.display = "none";
    }
});


// === LIVE FEED CONTROL ===
function startLiveFeed() {
    fetch('/start_live_feed', { method: 'POST' })
        .then(() => {
            const modal = new bootstrap.Modal(document.getElementById('liveFeedModal'));
            document.getElementById('liveFeedImg').src = '/video_feed';
            modal.show();
        });
}

function stopLiveFeed() {
    fetch('/stop_live_feed', { method: 'POST' })
        .then(() => {
            // Close modal if still open
            const modal = bootstrap.Modal.getInstance(document.getElementById('liveFeedModal'));
            if (modal) modal.hide();

            // Remove Bootstrap modal leftovers
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.overflow = '';
        })
        .then(() => {
            console.log("Live feed stopped. Reloading...");
            location.reload();
        })
        .catch(err => {
            console.error("Error stopping live feed:", err);
        });
}

document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById('schedule-form');

    form.addEventListener('submit', function(e) {
      e.preventDefault();

      const formData = new FormData(form);

      fetch('/add_schedule', {
        method: 'POST',
        body: formData
      })
      .then(res => res.json())
      .then(data => {
        const alertBox = document.getElementById('status-alert');
        alertBox.classList.remove('d-none', 'alert-danger');
        alertBox.classList.add('alert-success');
        alertBox.textContent = data.message;
      })
      .catch(err => {
        const alertBox = document.getElementById('status-alert');
        alertBox.classList.remove('d-none', 'alert-success');
        alertBox.classList.add('alert-danger');
        alertBox.textContent = 'Something went wrong while scheduling.';
      });
    });
  });

    function turnOnLight() {
        fetch('/light/on', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                document.getElementById("turnonlight").style.display = "none";
                document.getElementById("turnofflight").style.display = "block";
            });
    }

    function turnOffLight() {
        fetch('/light/off', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                document.getElementById("turnonlight").style.display = "block";
                document.getElementById("turnofflight").style.display = "none";
            });
    }



// === LIGHT CONTROL ===
function toggleArmLight() {
    const btn = document.querySelector('.btn-arm-light');
    lightArmed = !lightArmed;

    if (lightArmed) {
        btn.innerHTML = '<i class="bi bi-lightbulb-fill me-2"></i>Light Armed';
        btn.style.background = 'linear-gradient(135deg, #38a169, #48bb78)';
        showNotification('Security lights armed', 'success');
    } else {
        btn.innerHTML = '<i class="bi bi-lightbulb me-2"></i>Arm Light';
        btn.style.background = 'linear-gradient(135deg, var(--accent-orange), #ed8936)';
        showNotification('Security lights disarmed', 'warning');
    }
}

// === SIREN CONTROL ===
function toggleArmSiren() {
    const btn = document.querySelector('.btn-arm-siren');
    sirenArmed = !sirenArmed;

    if (sirenArmed) {
        btn.innerHTML = '<i class="bi bi-volume-up-fill me-2"></i>Siren Armed';
        btn.style.background = 'linear-gradient(135deg, #e53e3e, #f56565)';
        showNotification('Security siren armed', 'success');
    } else {
        btn.innerHTML = '<i class="bi bi-volume-up me-2"></i>Arm Siren';
        btn.style.background = 'linear-gradient(135deg, var(--accent-green), #48bb78)';
        showNotification('Security siren disarmed', 'warning');
    }
}

// === SURVEILLANCE STATE ===
 function pauseSurveillance() {
    console.log("in Pause sur main")
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");
    const systemStatus = document.getElementById("systemStatus");
    const statusIcon = document.getElementById("statusIcon");
    const statusText = document.getElementById("statusText");

    if (!pauseBtn || !resumeBtn) return;

    pauseBtn.style.display = "none";
    resumeBtn.style.display = "block";

    fetch("/pause", { method: "POST" })
        .then(() => {
            showNotification("Surveillance paused", "warning");
            // Update status to Offline
            systemStatus.classList.remove("text-success");
            systemStatus.classList.add("text-danger");
            statusIcon.classList.remove("bi-circle-fill");
            statusIcon.classList.add("bi-slash-circle-fill");
            statusText.textContent = "System Offline";
            systemStatus.style.border = "1px solid var(--accent-red)";
systemStatus.style.background = "rgba(229, 62, 62, 0.2)";

        })
        .catch(() => showNotification("Failed to pause surveillance", "danger"));
}     

function resumeSurveillance() {
    console.log("in Resume sur main")
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");
    const systemStatus = document.getElementById("systemStatus");
    const statusIcon = document.getElementById("statusIcon");
    const statusText = document.getElementById("statusText");

    if (!pauseBtn || !resumeBtn) return;

    pauseBtn.style.display = "block";
    resumeBtn.style.display = "none";

    fetch("/resume", { method: "POST" })
        .then(() => {
            showNotification("Surveillance resumed", "success");
            // Update status to Online
            systemStatus.classList.remove("text-danger");
            systemStatus.classList.add("text-success");
            statusIcon.classList.remove("bi-slash-circle-fill");
            statusIcon.classList.add("bi-circle-fill");
            statusText.textContent = "System Online";
            systemStatus.style.border = "1px solid var(--accent-green)";
systemStatus.style.background = "rgba(56, 161, 105, 0.2)";

        })
        .catch(() => showNotification("Failed to resume surveillance", "danger"));
}

// === UI-ONLY STATUS REFLECTORS (initial on load) ===
function pauseSurveillanceUIOnly() {
    console.log("In pause UI")

    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");
    const systemStatus = document.getElementById("systemStatus");
    const statusIcon = document.getElementById("statusIcon");
    const statusText = document.getElementById("statusText");

    if (!pauseBtn || !resumeBtn) return;

    pauseBtn.style.display = "none";
    resumeBtn.style.display = "block";

    systemStatus.classList.remove("text-success");
    systemStatus.classList.add("text-danger");
    statusIcon.classList.remove("bi-circle-fill");
    statusIcon.classList.add("bi-slash-circle-fill");
    statusText.textContent = "System Offline";
    systemStatus.style.border = "1px solid var(--accent-red)";
    systemStatus.style.background = "rgba(229, 62, 62, 0.2)";
}

function resumeSurveillanceUIOnly() {
    console.log("Inresume UI")
    const pauseBtn = document.getElementById("pauseBtn");
    const resumeBtn = document.getElementById("resumeBtn");
    const systemStatus = document.getElementById("systemStatus");
    const statusIcon = document.getElementById("statusIcon");
    const statusText = document.getElementById("statusText");

    if (!pauseBtn || !resumeBtn) return;

    pauseBtn.style.display = "block";
    resumeBtn.style.display = "none";

    systemStatus.classList.remove("text-danger");
    systemStatus.classList.add("text-success");
    statusIcon.classList.remove("bi-slash-circle-fill");
    statusIcon.classList.add("bi-circle-fill");
    statusText.textContent = "System Online";
    systemStatus.style.border = "1px solid var(--accent-green)";
    systemStatus.style.background = "rgba(56, 161, 105, 0.2)";
}


// === SYSTEM SHUTDOWN ===
function confirmShutdown() {
    if (confirm('Are you sure you want to shutdown the security system?')) {
        showNotification('System shutdown initiated...', 'danger');
        // Add your shutdown logic here
        setTimeout(() => {
            showNotification('System shutdown complete', 'danger');
        }, 3000);
    }
}

// === NOTIFICATION SYSTEM ===
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        backdrop-filter: blur(10px);
    `;

    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 3000);
}

