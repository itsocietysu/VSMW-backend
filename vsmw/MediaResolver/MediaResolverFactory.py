from vsmw.MediaResolver.ImageResolver import ImageResolver

class MediaResolverFactory:
    resolvers = {
        'image': ImageResolver,
        'equipment': ImageResolver,
    }
    separator = '\r\n'.encode()
    @staticmethod
    def produce(type, data):
        if type in MediaResolverFactory.resolvers:
            return MediaResolverFactory.resolvers[type](type, data)
        raise Exception('such media type not supported')
