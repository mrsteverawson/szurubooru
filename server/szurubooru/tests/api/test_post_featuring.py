import datetime
import pytest
from szurubooru import api, db, errors
from szurubooru.func import util, posts

@pytest.fixture
def test_ctx(context_factory, config_injector, user_factory, post_factory):
    config_injector({
        'privileges': {'posts:feature': 'regular_user'},
        'ranks': ['anonymous', 'regular_user'],
    })
    ret = util.dotdict()
    ret.context_factory = context_factory
    ret.user_factory = user_factory
    ret.post_factory = post_factory
    ret.api = api.PostFeatureApi()
    return ret

def test_featuring(test_ctx):
    db.session.add(test_ctx.post_factory(id=1))
    db.session.commit()
    assert posts.get_featured_post() is None
    assert not posts.get_post_by_id(1).is_featured
    result = test_ctx.api.post(
        test_ctx.context_factory(
            input={'id': 1},
            user=test_ctx.user_factory(rank='regular_user')))
    assert posts.get_featured_post() is not None
    assert posts.get_featured_post().post_id == 1
    assert posts.get_post_by_id(1).is_featured
    assert 'post' in result
    assert 'snapshots' in result
    assert 'id' in result['post']

def test_trying_to_feature_the_same_post_twice(test_ctx):
    db.session.add(test_ctx.post_factory(id=1))
    db.session.commit()
    test_ctx.api.post(
        test_ctx.context_factory(
            input={'id': 1},
            user=test_ctx.user_factory(rank='regular_user')))
    with pytest.raises(posts.PostAlreadyFeaturedError):
        test_ctx.api.post(
            test_ctx.context_factory(
                input={'id': 1},
                user=test_ctx.user_factory(rank='regular_user')))

def test_featuring_one_post_after_another(test_ctx, fake_datetime):
    db.session.add(test_ctx.post_factory(id=1))
    db.session.add(test_ctx.post_factory(id=2))
    db.session.commit()
    assert posts.get_featured_post() is None
    assert not posts.get_post_by_id(1).is_featured
    assert not posts.get_post_by_id(2).is_featured
    with fake_datetime('1997'):
        result = test_ctx.api.post(
            test_ctx.context_factory(
                input={'id': 1},
                user=test_ctx.user_factory(rank='regular_user')))
    with fake_datetime('1998'):
        result = test_ctx.api.post(
            test_ctx.context_factory(
                input={'id': 2},
                user=test_ctx.user_factory(rank='regular_user')))
    assert posts.get_featured_post() is not None
    assert posts.get_featured_post().post_id == 2
    assert not posts.get_post_by_id(1).is_featured
    assert posts.get_post_by_id(2).is_featured

def test_trying_to_feature_non_existing(test_ctx):
    with pytest.raises(posts.PostNotFoundError):
        test_ctx.api.post(
            test_ctx.context_factory(
                input={'id': 1},
                user=test_ctx.user_factory(rank='regular_user')))

def test_trying_to_feature_without_privileges(test_ctx):
    with pytest.raises(errors.AuthError):
        test_ctx.api.post(
            test_ctx.context_factory(
                input={'id': 1},
                user=test_ctx.user_factory(rank='anonymous')))