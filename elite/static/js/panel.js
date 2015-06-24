var panel = {
    init: function() {
        // Init elements
        // - Upload form
        panel.upload.form = document.querySelector('div#upload-form');

        panel.upload.name = panel.upload.form.querySelector('input#upload-name');
        panel.upload.category = panel.upload.form.querySelector('select#upload-category');
        panel.upload.description = panel.upload.form.querySelector('textarea#upload-description');
        panel.upload.file = panel.upload.form.querySelector('input#upload-file');
        panel.upload.progress = panel.upload.form.querySelector('div.progress');
        panel.upload.bar = panel.upload.progress.querySelector('div.bar');

        panel.upload.metadata = {};
        panel.upload.metadata.element = panel.upload.form.querySelector('div#upload-metadata');
        panel.upload.metadata.add = panel.upload.metadata.element.querySelector('button#upload-metadata-add');

        panel.upload.submit = panel.upload.form.querySelector('button[type="submit"]');

        // - Create category form
        panel.createCategory.form = document.querySelector('div#create-category-form');

        panel.createCategory.name = panel.createCategory.form.querySelector('input#create-category-name');
        panel.createCategory.parent = panel.createCategory.form.querySelector('select#create-category-parent');
        panel.createCategory.description = panel.createCategory.form.querySelector('textarea#create-category-description');

        panel.createCategory.submit = panel.createCategory.form.querySelector('button[type="submit"]');

        // Init events
        panel.upload.metadata.add.addEventListener('click', panel.events.onMetadataAdd);
        panel.upload.submit.addEventListener('click', panel.events.onUploadSubmit);
        panel.createCategory.submit.addEventListener('click', panel.events.onCreateCategorySubmit);

        // Init data
        panel.updateCategories();
    },

    updateCategories: function() {
        var categoriesSelects = document.querySelectorAll('select[data-name="categories"]');

        panel.upload.toggleLoading();
        panel.createCategory.toggleLoading();

        panel.api.getCategories(function(categories) {
            _.forEach(categoriesSelects, function(el) {
                panel.utils.clearSelect(el);

                var option = document.createElement('option');
                option.value = '';
                option.text = 'Root';
                el.add(option);

                _.forEach(categories, function(category) {
                    var option = document.createElement('option');
                    option.value = category.path;
                    option.text = category.name;

                    el.add(option);
                });
            });

            panel.upload.toggleLoading();
            panel.createCategory.toggleLoading();
        });
    },

    api: {
        getCategories: function(cb) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', '/api/categories', true);
            xhr.responseType = 'json';
            xhr.onload = function(e) {
                cb(xhr.response.categories);
            };
            xhr.send();
        },

        createCategory: function(data, cb) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/categories/create?key=' + panel.api.key, true);
            xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
            xhr.responseType = 'json';
            xhr.onload = function(e) {
                cb(xhr.response);
            };
            xhr.send(JSON.stringify(data));
        },

        createScreenshot: function(data, cb) {
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/screenshot/create?key=' + panel.api.key, true);
            xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8');
            xhr.responseType = 'json';
            xhr.onload = function(e) {
                cb(xhr.response);
            };
            xhr.send(JSON.stringify(data));
        },

        uploadScreenshot: function(path, file, cb, upload) {
            var data = new FormData();
            data.append('path', path);
            data.append('file', file);

            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/screenshot/upload?key=' + panel.api.key, true);
            xhr.responseType = 'json';
            xhr.onload = function(e) {
                cb(xhr.response);
            };
            xhr.upload.addEventListener('progress', upload.progress);
            xhr.upload.addEventListener('load', upload.done);
            xhr.send(data);
        },
    },

    events: {
        onMetadataAdd: function(e) {
            var el = document.createElement('div');
            el.classList.add('two');
            el.classList.add('fields');

            var name = panel.utils.createInputField('text', 'metadata-name', 'Name');
            el.appendChild(name);

            var value = panel.utils.createInputField('text', 'metadata-value', 'Value');
            el.appendChild(value);

            panel.upload.metadata.element.insertBefore(el, panel.upload.metadata.add);
        },

        onUploadSubmit: function(e) {
            panel.upload.toggleLoading();

            var data = {
                name: panel.upload.name.value,
                description: panel.upload.description.value,
                category: panel.upload.category.value,
                metadata: {},
            };
            var metadatas = panel.upload.metadata.element.querySelectorAll('div.fields');
            _.forEach(metadatas, function(el) {
                var name = el.querySelector('input[name="metadata-name"]').value;
                var value = el.querySelector('input[name="metadata-value"]').value;

                if (name != '') {
                    data.metadata[name] = value;
                }
            });

            panel.api.createScreenshot(data, function(res) {
                if (res.status != 'ok') {
                    console.log('Error:', res.message);
                    panel.upload.toggleLoading();
                    return;
                }

                panel.upload.progress.style.display = '';
                panel.api.uploadScreenshot(res.path, panel.upload.file.files[0], function(res) {
                    if (res.status != 'ok') {
                        console.log('Error:', res.message);
                        return;
                    }

                    console.log(res);
                }, {
                    progress: function(e) {
                        if (e.lengthComputable) {
                            var percent = e.loaded / e.total;
                            panel.upload.bar.style.width = (percent*100) + '%';
                        }
                    },
                    done: function() {
                        panel.upload.progress.style.display = 'none';
                        panel.upload.toggleLoading();
                    },
                });
            });
        },

        onCreateCategorySubmit: function(e) {
            panel.createCategory.toggleLoading();

            var data = {
                name: panel.createCategory.name.value,
                parent: panel.createCategory.parent.value,
                description: panel.createCategory.description.value,
            };

            panel.api.createCategory(data, function(res) {
                if (res.status != 'ok') {
                    console.log('Error:', res.message);
                    panel.createCategory.toggleLoading();
                    return;
                }

                panel.createCategory.toggleLoading();
                panel.updateCategories();
            });
        },
    },

    upload: {
        toggleLoading: function() {
            panel.upload.form.classList.toggle('loading');
        },
    },

    createCategory: {
        toggleLoading: function() {
            panel.createCategory.form.classList.toggle('loading');
        },
    },

    utils: {
        clearSelect: function(el) {
            for (var i = el.options.length - 1; i >= 0; i--) {
                el.remove(i);
            }
        },

        createInputField: function(type, name, placeholder) {
            var field = document.createElement('div');
            field.classList.add('field');

            var input = document.createElement('input');
            input.type = type;
            input.name = name;
            input.placeholder = placeholder;
            field.appendChild(input);

            return field;
        },
    },
};

window.onload = panel.init;
