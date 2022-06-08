/** @typedef {object} person
 * @property {string} handle
 * @property {string} display_name
 * @property {string} image
 * @property {number} solved
 * @property {number} score
 * @property {number} rank
 */

/**
 *
 * @param {person} data
 */
function createCard(data) {
  const elem = document.createElement("tr");
  elem.classList.add("grow");
  elem.innerHTML = `
    <td>
    <div class="d-flex align-items-center">
      <img
        src="${data.image}"
        class="circle-img circle-img--small mr-2"
        alt="User Img"
      />
      <div class="user-info__basic">
        <h5 class="mb-0">${data.display_name}</h5>
        <p class="text-muted mb-0"><a href="https://codeforces.com/profile/${data.handle}">${data.handle}</a></p>
      </div>
    </div>
  </td>
  <td>
    <div class="d-flex align-items-baseline">
      <h4 class="mr-1">${data.solved}</h4>
    </div>
  </td>
  <td>${data.score}</td>
    `;
  return elem;
}

/**
 *
 * @param {person[]} data
 */
function renderCards(data) {
  const table = document.getElementById("leaderboard-card-table");
  data.map((item) => {
    table.appendChild(createCard(item));
  });

  document.getElementById("top-1-img").setAttribute("src", data[1 - 1].image);
  document.getElementById("top-2-img").setAttribute("src", data[2 - 1].image);
  document.getElementById("top-3-img").setAttribute("src", data[3 - 1].image);

  document
    .getElementById("top-1-a")
    .setAttribute(
      "href",
      "https://codeforces.com/profile/" + data[1 - 1].handle
    );
  document
    .getElementById("top-2-a")
    .setAttribute(
      "href",
      "https://codeforces.com/profile/" + data[2 - 1].handle
    );
  document
    .getElementById("top-3-a")
    .setAttribute(
      "href",
      "https://codeforces.com/profile/" + data[3 - 1].handle
    );

  document.getElementById("top-1-a").innerHTML = data[1 - 1].handle;
  document.getElementById("top-2-a").innerHTML = data[2 - 1].handle;
  document.getElementById("top-3-a").innerHTML = data[3 - 1].handle;

  document.getElementById("top-1-prob").innerHTML = data[1 - 1].solved;
  document.getElementById("top-2-prob").innerHTML = data[2 - 1].solved;
  document.getElementById("top-3-prob").innerHTML = data[3 - 1].solved;

  document.getElementById("top-1-name").innerHTML = data[1 - 1].display_name;
  document.getElementById("top-2-name").innerHTML = data[2 - 1].display_name;
  document.getElementById("top-3-name").innerHTML = data[3 - 1].display_name;

  document.getElementById("top-1-score").innerHTML = data[1 - 1].score;
  document.getElementById("top-2-score").innerHTML = data[2 - 1].score;
  document.getElementById("top-3-score").innerHTML = data[3 - 1].score;
}

fetch("http://34.121.28.134/cf-tracker-api/get-ranks", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    month: new Date().getMonth(),
    year: new Date().getFullYear(),
  }),
})
  .then((res) => res.json())
  .then(renderCards)
  .catch((err) => console.error(err));
